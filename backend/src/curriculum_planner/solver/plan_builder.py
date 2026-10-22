"""Chuyển lời giải solver thành đối tượng `Plan` (kèm metrics, tiến độ khối và giải trình)."""

from __future__ import annotations

from curriculum_planner.analysis.context import PlanningContext
from curriculum_planner.domain.models import (
    STRATEGY_TITLES,
    BlockProgress,
    Plan,
    PlanTerm,
    ScheduledCourse,
    Strategy,
)
from curriculum_planner.explain.explainer import explain_course, highlights
from curriculum_planner.metrics import compute_metrics
from curriculum_planner.solver.runner import Solution


def course_badges(ctx: PlanningContext, c: str) -> list[str]:
    badges = []
    es, ls = ctx.es.get(c), ctx.ls.get(c)
    if c in ctx.mandatory and es is not None and ls is not None and ls - es <= 1:
        badges.append("găng")
    off = ctx.ds.offerings.get(c)
    if off is not None and (off.year_parity or off.offers_per_year <= 1):
        badges.append("hiếm mở")
    if ctx.risk.get(c, 0) >= 10:
        badges.append("rủi ro")
    if c in ctx.state.failed:
        badges.append("học lại")
    return badges


def build_plan(
    ctx: PlanningContext,
    strategy: Strategy,
    sol: Solution,
    explain: bool = True,
    plan_id: str | None = None,
) -> Plan:
    ds, cal = ctx.ds, ctx.calendar
    a, counted = sol.assignment, sol.counted
    grad = max(a.values()) if a else 0
    reg = ctx.regulation
    terms: list[PlanTerm] = []
    for t in range(grad + 1):
        cs = sorted(
            (c for c, tt in a.items() if tt == t),
            key=lambda c: (ds.block_kind.get(counted.get(c, ""), "z"), c),
        )
        sched = []
        for c in cs:
            course = ds.courses[c]
            leaf = counted.get(c)
            sched.append(
                ScheduledCourse(
                    course_id=c,
                    name=course.name,
                    credits=course.credits,
                    workload=course.workload,
                    counted_block=leaf,
                    block_kind=ds.block_kind.get(leaf, "other") if leaf else "other",
                    tags=course.tags,
                    badges=course_badges(ctx, c),
                    explanation=explain_course(ctx, c, a, counted, strategy) if explain else None,
                )
            )
        is_main = cal.is_main(t)
        final = t == grad
        terms.append(
            PlanTerm(
                index=t,
                term=cal.terms[t],
                label=cal.label(t),
                is_main=is_main,
                credits=sum(s.credits for s in sched),
                workload=sum(s.workload for s in sched),
                min_credits=(None if (final and reg.final_term_min_exempt) else ctx.wmin)
                if is_main
                else None,
                max_credits=ctx.cap(t),
                courses=sched,
            )
        )

    progress: list[BlockProgress] = []
    for b in ds.curriculum.all_blocks():
        spec = ds.block_specialization[b.id]
        if spec is not None and spec != ctx.spec:
            continue
        leaves = {lf.id for lf in b.leaves()}
        passed = sum(ds.courses[c].credits for c, lf in counted.items() if lf in leaves and c not in a)
        planned = sum(ds.courses[c].credits for c, lf in counted.items() if lf in leaves and c in a)
        progress.append(
            BlockProgress(
                block_id=b.id,
                name=b.name,
                depth=ds.depth[b.id],
                required=b.required_credits,
                passed_credits=passed,
                planned_credits=planned,
            )
        )

    metrics = compute_metrics(ctx, a, counted, sol.status, sol.solve_ms)
    return Plan(
        id=plan_id or strategy.value.lower(),
        strategy=strategy,
        title=STRATEGY_TITLES[strategy],
        specialization=ctx.spec,
        specialization_name=ds.specialization_name(ctx.spec),
        terms=terms,
        passed_assignment={c: lf for c, lf in counted.items() if c not in a},
        block_progress=progress,
        metrics=metrics,
        highlights=highlights(ctx, metrics),
    )
