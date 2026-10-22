"""Giải trình từng môn trong phương án: vì sao chọn, vì sao ở kỳ này, phụ thuộc, rủi ro.

"Vì sao không học sớm hơn" được trả lời bằng phép thử phản thực tế: dời môn sang kỳ sớm hơn
và để bộ kiểm chứng độc lập chỉ ra luật bị vi phạm.
"""

from __future__ import annotations

from curriculum_planner.analysis.context import PlanningContext
from curriculum_planner.analysis.graph import delta, next_offered
from curriculum_planner.domain.models import (
    DependencyType,
    Explanation,
    Reason,
    Strategy,
    TermKind,
)
from curriculum_planner.explain import messages_vi as msg
from curriculum_planner.verify.plan_verifier import verify_plan


def _name(ctx: PlanningContext, c: str) -> str:
    return f"{ctx.ds.courses[c].name} ({c})"


def _kinds(ctx: PlanningContext, c: str) -> str:
    off = ctx.ds.offerings[c]
    s = "/".join("Hè" if k == TermKind.HE else k.value for k in off.terms)
    if off.year_parity:
        s += " năm " + ("lẻ" if off.year_parity == "odd" else "chẵn")
    return s


def explain_course(
    ctx: PlanningContext,
    c: str,
    assignment: dict[str, int],
    counted: dict[str, str],
    strategy: Strategy,
) -> Explanation:
    ds, cal = ctx.ds, ctx.calendar
    t = assignment[c]
    course = ds.courses[c]

    # ---- vì sao chọn ----
    leaf = counted.get(c)
    succ_in_plan = [d.target for d in ds.successors.get(c, []) if d.target in assignment]
    selection: list[Reason] = []
    if leaf is not None and c in ds.blocks[leaf].mandatory_ids():
        kind = "MANDATORY"
        selection.append(
            Reason(code="MANDATORY", message=msg.SEL_MANDATORY.format(block=ds.blocks[leaf].name))
        )
    elif leaf is not None:
        kind = "ELECTIVE"
        b = ds.blocks[leaf]
        selection.append(
            Reason(code="ELECTIVE", message=msg.SEL_ELECTIVE.format(need=b.required_credits, block=b.name))
        )
        topics = []
        if ctx.profile.interests and ds.advisor:
            topics = [
                ds.advisor.topics.get(tag, tag)
                for tag in course.tags
                if ctx.profile.interests.get(tag, 0) >= 4
            ]
        if topics:
            selection.append(
                Reason(code="INTEREST", message=msg.WHY_INTEREST.format(topics=", ".join(topics)))
            )
        if succ_in_plan:
            selection.append(
                Reason(
                    code="UNLOCK",
                    message=msg.WHY_UNLOCK.format(targets=", ".join(_name(ctx, s) for s in succ_in_plan)),
                    courses=succ_in_plan,
                )
            )
        if not ds.successors.get(c):
            selection.append(Reason(code="LOW_RISK", message=msg.WHY_RISK_LOW))
    elif succ_in_plan:
        kind = "REQUIRED_AS_PREREQ"
        selection.append(
            Reason(
                code="PREREQ",
                message=msg.SEL_PREREQ.format(targets=", ".join(_name(ctx, s) for s in succ_in_plan)),
                courses=succ_in_plan,
            )
        )
    else:
        kind = "OTHER"
        selection.append(Reason(code="OTHER", message=msg.SEL_OTHER))

    # ---- môn trước ----
    requires: list[Reason] = []
    earliest = 0
    for d in ds.predecessors.get(c, []):
        a = d.source
        if ctx.dep_satisfied(d):
            requires.append(
                Reason(code=d.type.value, message=msg.REQ_PASSED.format(pre=_name(ctx, a)), courses=[a])
            )
        elif a in assignment:
            requires.append(
                Reason(
                    code=d.type.value,
                    message=msg.REQ_PLANNED.format(pre=_name(ctx, a), term=cal.label(assignment[a])),
                    courses=[a],
                    terms=[cal.label(assignment[a])],
                )
            )
            earliest = max(earliest, assignment[a] + delta(d))
    e_off = next_offered(ds, c, cal.terms, earliest)
    earliest_idx = e_off if e_off is not None else t

    # ---- vì sao ở kỳ này ----
    timing: list[Reason] = []
    delayed = False
    earlier_offered = [s for s in range(t) if ctx.offered(c, s)]
    if not earlier_offered:
        if t > 0:
            timing.append(
                Reason(
                    code="HC-10",
                    message=msg.TIME_BLOCKED_OFFER.format(term=cal.label(t - 1), kinds=_kinds(ctx, c)),
                )
            )
        timing.insert(0, Reason(code="EARLIEST", message=msg.TIME_EARLIEST))
    else:
        if course.final_term_only:
            timing.append(Reason(code="COURSE", message=msg.TIME_BLOCKED_FINAL))
        # thử dời sang tối đa 2 kỳ mở gần nhất phía trước
        any_free = None
        for s in reversed(earlier_offered[-2:]):
            moved = dict(assignment)
            moved[c] = s
            viol = verify_plan(ctx, moved, counted, check_preferences=False)
            reasons = _reasons_for(ctx, c, s, viol, assignment)
            if reasons:
                timing.extend(reasons)
            elif any_free is None:
                any_free = s
        if any_free is not None:
            delayed = True
            timing.append(
                Reason(
                    code="STRATEGY",
                    message=msg.TIME_STRATEGY.format(
                        term=cal.label(any_free), goal=msg.STRATEGY_GOAL[strategy.value]
                    ),
                    terms=[cal.label(any_free)],
                )
            )
        if t == earliest_idx and not delayed:
            timing.insert(0, Reason(code="EARLIEST", message=msg.TIME_EARLIEST))

    # ---- rủi ro ----
    retake_safe = ctx.safe(c, t) if ctx.safe_ls else None
    nxt = next_offered(ds, c, cal.terms, t + 1)
    unlocks = sorted({d.target for d in ds.successors.get(c, []) if d.target in ctx.candidates})
    es, ls = ctx.es.get(c), ctx.ls.get(c)
    critical = c in ctx.mandatory and es is not None and ls is not None and ls - es <= 1 and bool(unlocks)
    return Explanation(
        selection_kind=kind,
        selection=selection,
        timing=_dedupe(timing),
        earliest_term=cal.label(earliest_idx),
        delayed_by_strategy=delayed,
        requires=requires,
        unlocks=unlocks,
        on_critical_path=critical,
        risk_score=ctx.risk.get(c, 1),
        risk_factors=ctx.risk_factors.get(c, []),
        retake_safe=retake_safe,
        retake_term=cal.label(nxt) if nxt is not None else None,
    )


def _dedupe(rs: list[Reason]) -> list[Reason]:
    seen, out = set(), []
    for r in rs:
        if r.message not in seen:
            seen.add(r.message)
            out.append(r)
    return out


def _reasons_for(ctx: PlanningContext, c: str, s: int, viol, assignment) -> list[Reason]:
    cal, ds = ctx.calendar, ctx.ds
    out: list[Reason] = []
    for v in viol:
        if v.code in ("HC-04", "HC-05", "HC-06") and v.courses and v.courses[-1] == c:
            pre = v.courses[0]
            if pre in assignment:
                out.append(
                    Reason(
                        code=v.code,
                        message=msg.TIME_BLOCKED_PREREQ.format(
                            term=cal.label(s), pre=_name(ctx, pre), pre_term=cal.label(assignment[pre])
                        ),
                        courses=[pre],
                        terms=[cal.label(s)],
                    )
                )
            else:
                out.append(
                    Reason(
                        code=v.code,
                        message=msg.TIME_BLOCKED_NOT_PASSED.format(term=cal.label(s), pre=_name(ctx, pre)),
                        courses=[pre],
                    )
                )
        elif v.code == "HC-08" and s in v.terms and "trần" in v.message:
            out.append(
                Reason(
                    code="HC-08",
                    message=msg.TIME_BLOCKED_CAP.format(term=cal.label(s), cap=ctx.wmax),
                    terms=[cal.label(s)],
                )
            )
        elif v.code == "HC-10":
            out.append(
                Reason(
                    code="HC-10",
                    message=msg.TIME_BLOCKED_OFFER.format(term=cal.label(s), kinds=_kinds(ctx, c)),
                )
            )
        elif v.code == "COURSE" and "tích lũy" in v.message:
            out.append(
                Reason(
                    code="COURSE",
                    message=msg.TIME_BLOCKED_ACCUM.format(
                        term=cal.label(s), m=ds.courses[c].min_accumulated_credits
                    ),
                )
            )
        elif v.code == "COURSE" and "cuối" in v.message:
            out.append(Reason(code="COURSE", message=msg.TIME_BLOCKED_FINAL))
        elif v.code in ("HC-04", "HC-05", "HC-06") and v.courses and v.courses[0] == c:
            out.append(Reason(code=v.code, message=msg.TIME_BLOCKED_SUCC.format(term=cal.label(s))))
        else:
            out.append(
                Reason(
                    code=v.code, message=msg.TIME_BLOCKED_OTHER.format(term=cal.label(s), reason=v.message)
                )
            )
    return _dedupe(out)


def highlights(ctx: PlanningContext, metrics) -> list[str]:
    std_idx = ctx.calendar.standard_index
    out = [msg.HL_GRAD.format(term=metrics.graduation_term, n=metrics.main_terms_remaining)]
    total_std = ctx.ds.curriculum.standard_main_terms
    diff = metrics.total_main_terms - total_std
    if std_idx >= 0 or diff != 0:
        if diff < 0:
            out.append(msg.HL_VS_STANDARD_EARLY.format(n=-diff))
        elif diff > 0:
            out.append(msg.HL_VS_STANDARD_LATE.format(n=diff))
        else:
            out.append(msg.HL_VS_STANDARD_ON)
    out.append(msg.HL_LOAD.format(lo=metrics.load_min, hi=metrics.load_max, std=metrics.load_std))
    if metrics.summers_used:
        out.append(msg.HL_SUMMER.format(n=metrics.summers_used))
    out.append(msg.HL_RISK.format(pct=round(metrics.risk_coverage * 100)))
    if metrics.surplus_credits:
        out.append(msg.HL_SURPLUS.format(total=metrics.total_credits, surplus=metrics.surplus_credits))
    return out


__all__ = ["explain_course", "highlights", "DependencyType"]
