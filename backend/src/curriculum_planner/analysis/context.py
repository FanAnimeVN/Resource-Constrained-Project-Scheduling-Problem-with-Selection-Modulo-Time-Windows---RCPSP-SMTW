"""Gom mọi dữ kiện đã tiền xử lý cho một lần lập lộ trình (dùng chung cho solver, verifier, giải trình)."""

from __future__ import annotations

from dataclasses import dataclass, field

from curriculum_planner.analysis.calendar import Calendar, build_calendar
from curriculum_planner.analysis.graph import (
    earliest_starts,
    latest_starts,
    next_offered,
    offered_at,
    risk_scores,
)
from curriculum_planner.analysis.student_state import StudentState, build_state
from curriculum_planner.data.loader import Dataset
from curriculum_planner.domain.models import (
    Dependency,
    DependencyType,
    Preferences,
    Regulation,
    StudentProfile,
)


@dataclass
class PlanningContext:
    ds: Dataset
    regulation: Regulation
    profile: StudentProfile
    prefs: Preferences
    state: StudentState
    calendar: Calendar
    spec: str | None
    candidates: set[str]
    removed: dict[str, str]  # môn không thể học → lý do
    mandatory: set[str]  # môn bắt buộc CHƯA thỏa (theo chuyên ngành đã chọn)
    allowed_leaves: list[str]  # các khối lá được tính (khối chuyên ngành khác bị loại)
    wmin: int
    wmax: int
    wmax_summer: int
    personal_max: int | None
    es: dict[str, int | None] = field(default_factory=dict)
    ls: dict[str, int | None] = field(default_factory=dict)
    es_pred: dict[str, str | None] = field(default_factory=dict)
    risk: dict[str, int] = field(default_factory=dict)
    risk_factors: dict[str, list[str]] = field(default_factory=dict)
    pref: dict[str, int] = field(default_factory=dict)
    target_index: int = -1  # g_target cho BALANCED/RISK
    safe_ls: dict[str, int | None] = field(default_factory=dict)

    # ---- tiện ích ------------------------------------------------------------

    def dep_satisfied(self, d: Dependency) -> bool:
        if d.type == DependencyType.PREREQUISITE:
            return self.state.prereq_ok(d.source, d.min_grade)
        return d.source in self.state.attempted

    def credits(self, cid: str) -> int:
        return self.ds.courses[cid].credits

    def cap(self, t: int) -> int:
        if not self.calendar.is_main(t):
            return self.wmax_summer
        if self.personal_max is not None:
            return min(self.wmax, self.personal_max)
        return self.wmax

    def offered(self, cid: str, t: int) -> bool:
        return offered_at(self.ds, cid, self.calendar.terms[t])

    def allowed_terms(self, cid: str, prune: bool = True) -> list[int]:
        horizon = range(len(self.calendar.terms))
        if not prune:
            return list(horizon)
        es, ls = self.es.get(cid), self.ls.get(cid)
        if es is None or ls is None:
            return []
        return [t for t in horizon if es <= t <= ls and self.offered(cid, t)]

    def safe(self, cid: str, t: int) -> bool:
        """Rớt ở kỳ t vẫn còn lượt mở kế tiếp trước hạn muộn nhất (theo g_target)."""
        lim = self.safe_ls.get(cid)
        if lim is None:
            return False
        nxt = next_offered(self.ds, cid, self.calendar.terms, t + 1)
        return nxt is not None and nxt <= lim

    def leaf_members(self, leaf_id: str) -> list[str]:
        return [bc.id for bc in self.ds.blocks[leaf_id].courses]

    def available(self, cid: str) -> bool:
        return cid in self.state.satisfied or cid in self.candidates


def effective_load(reg: Regulation, profile: StudentProfile, gpa: float | None) -> tuple[int, int]:
    wmin, wmax = reg.min_credits_main, reg.max_credits_main
    for rule in reg.load_rules:
        applies = False
        if rule.when == "academic_warning":
            applies = profile.academic_warning
        elif rule.when.startswith("gpa_at_least:") and gpa is not None:
            applies = gpa >= float(rule.when.split(":", 1)[1])
        if applies:
            if rule.min_credits_main is not None:
                wmin = rule.min_credits_main
            if rule.max_credits_main is not None:
                wmax = rule.max_credits_main
    return wmin, wmax


def interest_vector(ds: Dataset, profile: StudentProfile, spec: str | None) -> dict[str, float]:
    if profile.interests:
        return {k: (v - 1) / 4 for k, v in profile.interests.items()}
    if ds.advisor and spec and spec in ds.advisor.specializations:
        return dict(ds.advisor.specializations[spec].topic_profile)
    return {}


def preference_scores(ds: Dataset, profile: StudentProfile, spec: str | None) -> dict[str, int]:
    vec = interest_vector(ds, profile, spec)
    out: dict[str, int] = {}
    for cid, c in ds.courses.items():
        ws = [vec.get(tag, 0.0) for tag in c.tags]
        if not ws:
            out[cid] = 0
            continue
        out[cid] = round(10 * (0.6 * max(ws) + 0.4 * sum(ws) / len(ws)))
    return out


def build_context(
    ds: Dataset,
    profile: StudentProfile,
    regulation_id: str | None = None,
    prefs: Preferences | None = None,
    spec: str | None = None,
    mode: str = "optimize",
    regulation: Regulation | None = None,
) -> PlanningContext:
    prefs = prefs or profile.preferences
    reg = regulation or ds.regulation(regulation_id)
    state = build_state(ds, profile, prefs)
    cal = build_calendar(
        profile.cohort_year,
        profile.next_term,
        reg.max_main_terms,
        ds.curriculum.standard_main_terms,
        prefs.summer_enabled,
        extra_main_terms=4 if mode == "explain" else 0,
    )
    if mode == "optimize":
        cal.terms = cal.terms[: cal.deadline_index + 1]
    wmin, wmax = effective_load(reg, profile, state.gpa)

    if spec is None and ds.curriculum.specializations:
        spec = profile.declared_specialization
    allowed_leaves = [
        leaf.id
        for leaf in ds.curriculum.leaf_blocks()
        if ds.block_specialization[leaf.id] is None or ds.block_specialization[leaf.id] == spec
    ]

    # ---- ứng viên ----
    pool = set(ds.course_leaf_blocks) | {d.source for d in ds.dependencies if d.source in ds.courses}
    removed: dict[str, str] = {}
    candidates: set[str] = set()
    excl_with: dict[str, list[str]] = {}
    for a, b in ds.exclusive_pairs:
        excl_with.setdefault(a, []).append(b)
        excl_with.setdefault(b, []).append(a)
    for cid in sorted(pool):
        c = ds.courses[cid]
        if cid in state.satisfied:
            continue
        if not c.is_active:
            removed[cid] = "đã ngừng giảng dạy"
            continue
        if cid not in ds.offerings:
            removed[cid] = "chưa có lịch mở môn"
            continue
        blocking = [o for o in excl_with.get(cid, []) if o in state.satisfied]
        if blocking:
            removed[cid] = f"loại trừ với môn đã đạt {', '.join(blocking)}"
            continue
        if c.min_gpa is not None and state.gpa is not None and state.gpa < c.min_gpa:
            removed[cid] = f"cần GPA ≥ {c.min_gpa} (GPA hiện tại {state.gpa})"
            continue
        candidates.add(cid)

    mandatory: set[str] = set()
    for leaf_id in allowed_leaves:
        for m in ds.blocks[leaf_id].mandatory_ids():
            if m not in state.satisfied:
                mandatory.add(m)

    ctx = PlanningContext(
        ds=ds,
        regulation=reg,
        profile=profile,
        prefs=prefs,
        state=state,
        calendar=cal,
        spec=spec,
        candidates=candidates,
        removed=removed,
        mandatory=mandatory,
        allowed_leaves=allowed_leaves,
        wmin=wmin,
        wmax=wmax,
        wmax_summer=reg.max_credits_summer,
        personal_max=prefs.personal_max_credits,
    )

    terms = cal.terms
    cum, acc = [], 0
    for t in range(len(terms)):
        cum.append(acc)
        acc += ctx.cap(t)
    ctx.es, ctx.es_pred = earliest_starts(ds, terms, candidates, ctx.dep_satisfied, cum, state.passed_credits)
    deadline = min(cal.deadline_index, len(terms) - 1)
    required = mandatory & candidates
    ctx.ls = latest_starts(ds, terms, candidates, required, ctx.dep_satisfied, deadline)
    ctx.risk, ctx.risk_factors = risk_scores(ds, candidates, state.failed)
    ctx.pref = preference_scores(ds, profile, spec)
    return ctx


def finalize_target(ctx: PlanningContext, g_fast: int) -> None:
    """Đặt g_target = max(g_fast, kỳ chuẩn hoặc kỳ SV mong muốn) và tính LS phục vụ 'đệm học lại'."""
    target = ctx.calendar.standard_index
    if ctx.prefs.target_graduation_term is not None:
        target = ctx.calendar.index_at_or_before(ctx.prefs.target_graduation_term)
    target = max(g_fast, min(target, len(ctx.calendar.terms) - 1))
    ctx.target_index = target
    required = ctx.mandatory & ctx.candidates
    ctx.safe_ls = latest_starts(
        ctx.ds, ctx.calendar.terms, ctx.candidates, required, ctx.dep_satisfied, target
    )
