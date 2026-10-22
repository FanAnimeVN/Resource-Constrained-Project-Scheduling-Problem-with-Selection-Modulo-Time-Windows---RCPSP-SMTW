"""Dựng mô hình CP-SAT tích hợp: CHỌN môn + XẾP kỳ trong cùng một mô hình.

Hai chế độ:
- `optimize`: cắt tỉa biến theo cửa sổ [ES, LS] ∩ kỳ mở môn; ràng buộc không gắn literal.
- `explain`:  không cắt tỉa, mỗi nhóm luật nghiệp vụ gắn một assumption literal để trích MUS.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from curriculum_planner.analysis.context import PlanningContext
from curriculum_planner.domain.models import DependencyType, SelectionRule, TermKind
from curriculum_planner.explain import messages_vi as msg


@dataclass
class GroupInfo:
    key: tuple
    code: str
    message: str
    courses: list[str] = field(default_factory=list)
    terms: list[str] = field(default_factory=list)
    relaxable: bool = False


@dataclass
class BuiltModel:
    ctx: PlanningContext
    mode: str
    model: cp_model.CpModel
    H: int
    allowed: dict[str, list[int]]
    x: dict[tuple[str, int], cp_model.IntVar]
    sel: dict[str, cp_model.IntVar]
    y: dict[tuple[str, str], cp_model.IntVar]
    le: list[cp_model.IntVar]
    load: list[cp_model.IntVar]
    groups: dict[tuple, tuple[cp_model.IntVar, GroupInfo]]
    objectives: dict[str, object] = field(default_factory=dict)

    @property
    def grad(self):
        return sum(self.le) - 1

    def assumptions(self) -> list[cp_model.IntVar]:
        return [lit for lit, _ in self.groups.values()]


class _Builder:
    def __init__(self, ctx: PlanningContext, mode: str):
        self.ctx = ctx
        self.mode = mode
        self.m = cp_model.CpModel()
        self.groups: dict[tuple, tuple[cp_model.IntVar, GroupInfo]] = {}
        self._false = self.m.new_constant(0)

    # ---- nhóm ràng buộc ----------------------------------------------------

    def lit(self, key: tuple, code: str, message: str, courses=(), terms=(), relaxable=False):
        if self.mode != "explain":
            return None
        if key not in self.groups:
            v = self.m.new_bool_var("g_" + "_".join(map(str, key)))
            self.groups[key] = (v, GroupInfo(key, code, message, list(courses), list(terms), relaxable))
        return self.groups[key][0]

    def add(self, ct, lit, extra=()):
        enf = [e for e in ([lit] if lit is not None else []) + list(extra)]
        if enf:
            ct.only_enforce_if(enf)
        return ct

    def fail(self, lit, extra=()):
        """Ràng buộc luôn sai (dùng khi một yêu cầu không thể thỏa)."""
        self.add(self.m.add(self._false >= 1), lit, extra)

    def ge(self, expr, value, lit, extra=()):
        """expr ≥ value, xử lý cả trường hợp expr là hằng số (tổng rỗng)."""
        if isinstance(expr, int):
            if expr < value:
                self.fail(lit, extra)
            return
        self.add(self.m.add(expr >= value), lit, extra)

    # ---- dựng ----------------------------------------------------------------

    def build(self) -> BuiltModel:
        ctx, m = self.ctx, self.m
        ds, cal = ctx.ds, ctx.calendar
        H = len(cal.terms)
        prune = self.mode == "optimize"
        cands = sorted(ctx.candidates)
        name = lambda c: f"{ds.courses[c].name} ({c})"  # noqa: E731

        allowed = {c: ctx.allowed_terms(c, prune=prune) for c in cands}
        x = {(c, t): m.new_bool_var(f"x_{c}_{t}") for c in cands for t in allowed[c]}
        sel: dict[str, cp_model.IntVar] = {}
        for c in cands:
            s = m.new_bool_var(f"sel_{c}")
            m.add(sum(x[c, t] for t in allowed[c]) == s)
            sel[c] = s

        # ---- kỳ tốt nghiệp: le[t] = 1 ⇔ t ≤ grad ----
        le = [m.new_bool_var(f"le_{t}") for t in range(H)]
        if H:
            m.add(le[0] == 1)
        for t in range(H - 1):
            m.add(le[t] >= le[t + 1])
        for (_c, t), v in x.items():
            m.add(v <= le[t])

        load = []
        for t in range(H):
            lv = m.new_int_var(0, 60, f"load_{t}")
            m.add(lv == sum(ds.courses[c].credits * x[c, t] for c in cands if (c, t) in x))
            load.append(lv)
        for t in range(H):
            nxt = le[t + 1] if t + 1 < H else None
            # fin[t] = le[t] − le[t+1]: kỳ tốt nghiệp phải có ít nhất 1 môn
            m.add(load[t] >= le[t] - (nxt if nxt is not None else 0))

        # ---- HC-10 kỳ mở môn (chỉ ở explain; optimize đã cắt tỉa) ----
        if not prune:
            for c in cands:
                off = ds.offerings[c]
                kinds = "/".join(k.value if k != TermKind.HE else "Hè" for k in off.terms)
                if off.year_parity:
                    kinds += " (năm " + ("lẻ" if off.year_parity == "odd" else "chẵn") + ")"
                bad = [t for t in allowed[c] if not ctx.offered(c, t)]
                if bad:
                    g = self.lit(
                        ("OFFER", c), "HC-10", msg.GROUP["OFFER"].format(course=name(c), kinds=kinds), [c]
                    )
                    for t in bad:
                        self.add(m.add(x[c, t] == 0), g)

        # ---- HC-04/05/06 phụ thuộc ----
        for d in ds.dependencies:
            if d.type == DependencyType.MUTUALLY_EXCLUSIVE or d.target not in ctx.candidates:
                continue
            if ctx.dep_satisfied(d):
                continue
            a, b = d.source, d.target
            code = {"PREREQUISITE": "HC-04", "PRE_COURSE": "HC-05", "CO_REQUISITE": "HC-06"}[d.type.value]
            g = self.lit(("DEP", a, b), code, msg.GROUP[d.type.value].format(a=name(a), b=name(b)), [a, b])
            if a not in ctx.candidates:
                self.add(m.add(sel[b] == 0), g)
                continue
            for t in allowed[b]:
                if d.type == DependencyType.CO_REQUISITE:
                    before = [x[a, s] for s in allowed[a] if s <= t]
                else:
                    before = [x[a, s] for s in allowed[a] if s < t]
                self.add(m.add(x[b, t] <= sum(before)), g)

        # ---- khối kiến thức (HC-03) + tổng (HC-01) ----
        allowed_leaves = ctx.allowed_leaves
        y: dict[tuple[str, str], cp_model.IntVar] = {}
        for leaf_id in allowed_leaves:
            for c in ctx.leaf_members(leaf_id):
                if ctx.available(c):
                    v = m.new_bool_var(f"y_{c}_{leaf_id}")
                    if c in sel:
                        m.add(v <= sel[c])
                    y[c, leaf_id] = v
        by_course: dict[str, list[cp_model.IntVar]] = {}
        for (c, _b), v in y.items():
            by_course.setdefault(c, []).append(v)
        for c, vs in by_course.items():
            if not ctx.regulation.allow_double_count_across_blocks:
                m.add(sum(vs) <= 1)
            if c in sel:
                # không xếp môn "vô ích": môn được chọn phải được tính vào ít nhất một khối
                m.add(sel[c] <= sum(vs))

        allowed_set = set(allowed_leaves)
        for b in ds.blocks.values():
            spec = ds.block_specialization[b.id]
            if spec is not None and spec != ctx.spec:
                continue
            leaves = [lf.id for lf in b.leaves() if lf.id in allowed_set]
            terms_ = [ds.courses[c].credits * v for (c, lb), v in y.items() if lb in leaves]
            if b.rule == SelectionRule.PICK_K_OF_N and b.k:
                g = self.lit(("BLOCK_K", b.id), "HC-03", msg.GROUP["BLOCK_K"].format(block=b.name, k=b.k))
                self.ge(sum(v for (c, lb), v in y.items() if lb in leaves), b.k, g)
            if b.required_credits > 0:
                g = self.lit(
                    ("BLOCK", b.id), "HC-03", msg.GROUP["BLOCK"].format(block=b.name, need=b.required_credits)
                )
                self.ge(sum(terms_), b.required_credits, g)
            if b.is_leaf:
                for c in b.mandatory_ids():
                    g = self.lit(("MAND", c), "HC-03", msg.GROUP["MAND"].format(course=name(c)), [c])
                    if (c, b.id) in y:
                        self.add(m.add(y[c, b.id] == 1), g)
                    else:
                        self.fail(g)

        total_expr = sum(
            ds.courses[c].credits * v for (c, _lb), v in y.items() if ds.courses[c].counts_toward_total
        )
        total_req = ds.curriculum.total_credits_required
        g = self.lit(("TOTAL",), "HC-01", msg.GROUP["TOTAL"].format(total=total_req))
        if ds.curriculum.credit_rule == "exact" and not isinstance(total_expr, int):
            self.add(m.add(total_expr == total_req), g)
        else:
            self.ge(total_expr, total_req, g)

        # ---- HC-07 loại trừ ----
        for a, b in ds.exclusive_pairs:
            if not (ctx.available(a) and ctx.available(b)):
                continue
            g = self.lit(("EXCL", a, b), "HC-07", msg.GROUP["EXCL"].format(a=name(a), b=name(b)), [a, b])
            if a in sel and b in sel:
                self.add(m.add(sel[a] + sel[b] <= 1), g)
            ys = by_course.get(a, []) + by_course.get(b, [])
            if ys:
                self.add(m.add(sum(ys) <= 1), g)

        # ---- HC-08 / HC-09 tải học kỳ ----
        reg = ctx.regulation
        for t in range(H):
            term = cal.terms[t]
            label = term.label
            if term.is_main:
                g = self.lit(
                    ("CAP", t),
                    "HC-08",
                    msg.GROUP["CAP"].format(term=label, cap=ctx.wmax),
                    terms=[label],
                    relaxable=True,
                )
                self.add(m.add(load[t] <= ctx.wmax), g)
                if ctx.personal_max is not None:
                    g = self.lit(
                        ("PERSONAL_CAP",),
                        "PREF",
                        msg.GROUP["PERSONAL_CAP"].format(cap=ctx.personal_max),
                        relaxable=True,
                    )
                    self.add(m.add(load[t] <= ctx.personal_max), g)
                if ctx.wmin > 0:
                    gate = (
                        le[t + 1]
                        if (reg.final_term_min_exempt and t + 1 < H)
                        else (None if reg.final_term_min_exempt else le[t])
                    )
                    if gate is not None:
                        g = self.lit(
                            ("FLOOR", t),
                            "HC-08",
                            msg.GROUP["FLOOR"].format(term=label, floor=ctx.wmin),
                            terms=[label],
                            relaxable=True,
                        )
                        extra = [gate]
                        if reg.allow_empty_main_terms:
                            enrolled = m.new_bool_var(f"enr_{t}")
                            m.add(load[t] >= 1).only_enforce_if(enrolled)
                            m.add(load[t] == 0).only_enforce_if(enrolled.Not())
                            extra.append(enrolled)
                        self.add(m.add(load[t] >= ctx.wmin), g, extra)
            else:
                g = self.lit(
                    ("SUMMER_CAP", t),
                    "HC-09",
                    msg.GROUP["SUMMER_CAP"].format(term=label, cap=ctx.wmax_summer),
                    terms=[label],
                    relaxable=True,
                )
                self.add(m.add(load[t] <= ctx.wmax_summer), g)

        # ---- HC-11 hạn chót (explain: horizon dài hơn hạn) ----
        grad = sum(le) - 1
        D = cal.deadline_index
        if H and D < H - 1:
            g = self.lit(
                ("DEADLINE",),
                "HC-11",
                msg.GROUP["DEADLINE"].format(deadline=cal.deadline_term.label),
                terms=[cal.deadline_term.label],
                relaxable=True,
            )
            self.add(m.add(grad <= D), g)

        # ---- điều kiện môn ----
        base = ctx.state.passed_credits
        for c in cands:
            course = ds.courses[c]
            if course.min_accumulated_credits:
                M = course.min_accumulated_credits
                g = self.lit(("ACCUM", c), "COURSE", msg.GROUP["ACCUM"].format(course=name(c), m=M), [c])
                for t in allowed[c]:
                    self.ge(sum(load[:t]), M - base, g, [x[c, t]])
            if course.final_term_only:
                g = self.lit(("FINAL", c), "COURSE", msg.GROUP["FINAL"].format(course=name(c)), [c])
                for t in allowed[c]:
                    if t + 1 < H:
                        self.add(m.add(le[t + 1] == 0), g, [x[c, t]])

        # ---- tùy chọn của sinh viên ----
        prefs = ctx.prefs
        for p in prefs.pinned:
            c = p.course
            label = p.term.label
            g = self.lit(
                ("PIN", c),
                "PREF",
                msg.GROUP["PIN"].format(course=c, term=label),
                [c],
                [label],
                relaxable=True,
            )
            t = cal.index_of(p.term)
            if c in sel and t is not None and (c, t) in x:
                self.add(m.add(x[c, t] == 1), g)
            elif c in ctx.state.satisfied:
                continue
            else:
                self.fail(g)
        for c in prefs.excluded:
            if c in sel:
                g = self.lit(
                    ("EXCLUDED", c), "PREF", msg.GROUP["EXCLUDED"].format(course=c), [c], relaxable=True
                )
                self.add(m.add(sel[c] == 0), g)
        if prefs.target_graduation_term is not None and H:
            tg = cal.index_at_or_before(prefs.target_graduation_term)
            g = self.lit(
                ("TARGET",),
                "PREF",
                msg.GROUP["TARGET"].format(term=prefs.target_graduation_term.label),
                relaxable=True,
            )
            if tg < 0:
                self.fail(g)
            else:
                self.add(m.add(grad <= tg), g)

        built = BuiltModel(
            ctx=ctx,
            mode=self.mode,
            model=m,
            H=H,
            allowed=allowed,
            x=x,
            sel=sel,
            y=y,
            le=le,
            load=load,
            groups=self.groups,
        )
        if self.mode == "optimize":
            _add_objective_exprs(built)
        return built


def _add_objective_exprs(b: BuiltModel) -> None:
    ctx, m = b.ctx, b.model
    ds, cal = ctx.ds, ctx.calendar
    H = b.H
    used_summer = []
    for t in range(H):
        if not cal.is_main(t):
            u = m.new_bool_var(f"usedS_{t}")
            m.add(b.load[t] >= 1).only_enforce_if(u)
            m.add(b.load[t] == 0).only_enforce_if(u.Not())
            used_summer.append(u)
    sq = []
    for t in range(H):
        if cal.is_main(t):
            s = m.new_int_var(0, 3600, f"sq_{t}")
            m.add_multiplication_equality(s, [b.load[t], b.load[t]])
            sq.append(s)
    maxload = m.new_int_var(0, 60, "maxload")
    for t in range(H):
        if cal.is_main(t):
            m.add(maxload >= b.load[t])
    peak = m.new_int_var(0, 200, "peak")
    for t in range(H):
        m.add(peak >= sum(ds.courses[c].workload * v for (c, tt), v in b.x.items() if tt == t))
    electives = [c for c in b.sel if c not in ctx.mandatory]
    b.objectives = {
        "grad": b.grad,
        "summer": sum(used_summer),
        "credits": sum(ds.courses[c].credits * s for c, s in b.sel.items()),
        "front": sum(ds.courses[c].credits * t * v for (c, t), v in b.x.items()),
        "sq": sum(sq),
        "maxload": maxload,
        "peak": peak,
        "early": sum(ctx.risk.get(c, 1) * t * v for (c, t), v in b.x.items()),
        "pref": sum(ctx.pref.get(c, 0) * ds.courses[c].credits * b.sel[c] for c in electives),
    }


def add_safe_objective(b: BuiltModel) -> None:
    """f_safe: trọng số rủi ro của các môn BẮT BUỘC có đệm học lại (môn tự chọn rớt thì thay môn khác được).

    Phụ thuộc g_target nên phải gọi sau `finalize_target`.
    """
    ctx = b.ctx
    b.objectives["safe"] = sum(
        ctx.risk.get(c, 1) * v for (c, t), v in b.x.items() if c in ctx.mandatory and ctx.safe(c, t)
    )


def build_model(ctx: PlanningContext, mode: str = "optimize") -> BuiltModel:
    return _Builder(ctx, mode).build()
