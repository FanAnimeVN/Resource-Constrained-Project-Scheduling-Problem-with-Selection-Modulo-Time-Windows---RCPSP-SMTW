"""Chỉ số so sánh phương án."""

from __future__ import annotations

import math
from collections import Counter

from curriculum_planner.analysis.context import PlanningContext
from curriculum_planner.domain.models import Plan, PlanMetrics


def compute_metrics(
    ctx: PlanningContext, assignment: dict[str, int], counted: dict[str, str], status: str, solve_ms: int
) -> PlanMetrics:
    ds, cal = ctx.ds, ctx.calendar
    H = len(cal.terms)
    loads = [0] * H
    wl = [0] * H
    for c, t in assignment.items():
        loads[t] += ds.courses[c].credits
        wl[t] += ds.courses[c].workload
    grad = max(assignment.values()) if assignment else 0
    main = [loads[t] for t in range(grad + 1) if cal.is_main(t)]
    mean = sum(main) / len(main) if main else 0.0
    std = math.sqrt(sum((v - mean) ** 2 for v in main) / len(main)) if main else 0.0
    planned = sum(ds.courses[c].credits for c in assignment)
    total = sum(ds.courses[c].credits for c in counted if ds.courses[c].counts_toward_total)
    # độ phủ đệm học lại tính trên môn bắt buộc (môn tự chọn rớt có thể thay bằng môn khác)
    mand = [c for c in assignment if c in ctx.mandatory]
    risk_total = sum(ctx.risk.get(c, 1) for c in mand)
    risk_safe = sum(ctx.risk.get(c, 1) for c in mand if ctx.safe(c, assignment[c]))
    electives = [c for c in assignment if c not in ctx.mandatory]
    el_credits = sum(ds.courses[c].credits for c in electives)
    interest = (
        sum(ctx.pref.get(c, 0) * ds.courses[c].credits for c in electives) / (10 * el_credits)
        if el_credits
        else 0.0
    )
    tag_credits: Counter[str] = Counter()
    for c in electives:
        for tag in ds.courses[c].tags[:1]:
            tag_credits[tag] += ds.courses[c].credits
    focus = (tag_credits.most_common(1)[0][1] / el_credits) if el_credits and tag_credits else 0.0
    completed_main = _completed_main_terms(ctx)
    return PlanMetrics(
        graduation_term=cal.label(grad),
        graduation_index=grad,
        main_terms_remaining=sum(1 for t in range(grad + 1) if cal.is_main(t)),
        total_main_terms=completed_main + sum(1 for t in range(grad + 1) if cal.is_main(t)),
        planned_credits=planned,
        total_credits=total,
        surplus_credits=max(0, total - ds.curriculum.total_credits_required),
        load_std=round(std, 2),
        load_max=max(main) if main else 0,
        load_min=min(main) if main else 0,
        peak_workload=max(wl) if wl else 0,
        summers_used=sum(1 for t in range(H) if not cal.is_main(t) and loads[t] > 0),
        risk_coverage=round(risk_safe / risk_total, 3) if risk_total else 1.0,
        interest_score=round(interest, 3),
        focus_ratio=round(focus, 3),
        solver_status=status,
        solve_ms=solve_ms,
    )


def _completed_main_terms(ctx: PlanningContext) -> int:
    nt = ctx.profile.next_term
    n = (nt.year - ctx.profile.cohort_year) * 2 + (
        0 if nt.kind.value == "HK1" else 1 if nt.kind.value == "HK2" else 2
    )
    return max(0, n)


def plan_distance(a: Plan, b: Plan) -> int:
    """Số môn khác kỳ + hiệu đối xứng tập môn + chênh kỳ tốt nghiệp."""
    aa, bb = a.assignment(), b.assignment()
    moved = sum(1 for c in set(aa) & set(bb) if aa[c] != bb[c])
    sym = len(set(aa) ^ set(bb))
    return moved + sym + abs(a.metrics.graduation_index - b.metrics.graduation_index)
