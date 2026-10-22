"""Điều phối: kiểm tra dữ liệu → chẩn đoán nhanh → giải các chiến lược → kiểm chứng → giải trình."""

from __future__ import annotations

import logging
import time

from pydantic import BaseModel, Field

from curriculum_planner.advisor.specialization import recommend_specializations
from curriculum_planner.analysis.context import PlanningContext, build_context
from curriculum_planner.analysis.prechecks import _block_deficit, run_prechecks
from curriculum_planner.data.loader import Dataset
from curriculum_planner.domain.models import (
    InfeasibilityReport,
    Issue,
    Plan,
    PlanMetrics,
    Preferences,
    Regulation,
    Strategy,
    StudentProfile,
    ValidationReport,
)
from curriculum_planner.explain import messages_vi as msg
from curriculum_planner.metrics import plan_distance
from curriculum_planner.solver.mus import explain_infeasibility
from curriculum_planner.solver.plan_builder import build_plan
from curriculum_planner.solver.strategies import solve_all
from curriculum_planner.validation.validator import validate_dataset
from curriculum_planner.verify.plan_verifier import verify_plan

log = logging.getLogger(__name__)


class ComparisonRow(BaseModel):
    plan_id: str
    strategy: Strategy
    title: str
    metrics: PlanMetrics
    duplicate_of: str | None = None


class Comparison(BaseModel):
    rows: list[ComparisonRow]
    distances: dict[str, dict[str, int]]


class PlanResult(BaseModel):
    status: str  # OK | INFEASIBLE | COMPLETED | DATA_ERROR
    student_id: str
    dataset: str
    regulation: str
    specialization: str | None = None
    specialization_name: str | None = None
    specialization_source: str | None = None
    plans: list[Plan] = Field(default_factory=list)
    comparison: Comparison | None = None
    infeasibility: InfeasibilityReport | None = None
    validation: ValidationReport | None = None
    warnings: list[str] = Field(default_factory=list)
    graduation_conditions: list[str] = Field(default_factory=list)
    gpa: float | None = None
    passed_credits: int = 0
    timings_ms: dict[str, int] = Field(default_factory=dict)


_VALIDATION_CACHE: dict[int, tuple[Dataset, ValidationReport]] = {}


def cached_validation(ds: Dataset) -> ValidationReport:
    hit = _VALIDATION_CACHE.get(id(ds))
    if hit is None or hit[0] is not ds:
        hit = (ds, validate_dataset(ds))
        _VALIDATION_CACHE[id(ds)] = hit
    return hit[1]


def resolve_specialization(
    ds: Dataset, profile: StudentProfile, prefs: Preferences, regulation_id: str | None
) -> tuple[str | None, str | None]:
    valid = {s.id for s in ds.curriculum.specializations}
    if not valid:
        return None, None
    if prefs.specialization and prefs.specialization != "auto" and prefs.specialization in valid:
        return prefs.specialization, "preference"
    if profile.declared_specialization in valid:
        return profile.declared_specialization, "declared"
    advice = recommend_specializations(ds, profile, regulation_id, prefs)
    if advice.top:
        return advice.top, "advisor"
    return sorted(valid)[0], "default"


def plan_for_student(
    ds: Dataset,
    profile: StudentProfile,
    regulation_id: str | None = None,
    prefs: Preferences | None = None,
    strategies: list[Strategy] | None = None,
    explain: bool = True,
    regulation: Regulation | None = None,
    time_limit: float | None = None,
) -> PlanResult:
    t0 = time.perf_counter()
    prefs = prefs or profile.preferences
    reg = regulation or ds.regulation(regulation_id)
    result = PlanResult(
        status="OK",
        student_id=profile.id,
        dataset=ds.id,
        regulation=reg.id,
        graduation_conditions=ds.curriculum.graduation_conditions,
    )
    timings: dict[str, int] = {}

    report = cached_validation(ds)
    if not report.ok:
        result.status = "DATA_ERROR"
        result.validation = report
        return result

    spec, source = resolve_specialization(ds, profile, prefs, reg.id)
    result.specialization, result.specialization_source = spec, source
    result.specialization_name = ds.specialization_name(spec)
    timings["specialization"] = int((time.perf_counter() - t0) * 1000)

    ctx = build_context(ds, profile, prefs=prefs, spec=spec, regulation=reg)
    result.warnings.extend(ctx.state.warnings)
    result.gpa = ctx.state.gpa
    result.passed_credits = ctx.state.passed_credits
    for c, why in sorted(ctx.removed.items()):
        if c in ctx.mandatory:
            result.warnings.append(f"Môn bắt buộc {ds.courses[c].name} ({c}) không thể đăng ký: {why}.")

    if not ctx.mandatory and _block_deficit(ctx) == 0:
        result.status = "COMPLETED"
        result.warnings.append(msg.COMPLETED)
        return result

    pre = run_prechecks(ctx)
    timings["prechecks"] = int((time.perf_counter() - t0) * 1000)
    if pre:
        return _infeasible(result, ds, profile, reg, prefs, spec, pre, timings, t0)

    results, dup = solve_all(ctx, strategies, time_limit=time_limit)
    timings["solve"] = int((time.perf_counter() - t0) * 1000)
    if not results:
        return _infeasible(result, ds, profile, reg, prefs, spec, [], timings, t0)

    plans: list[Plan] = []
    for r in results:
        sol = r.solution
        violations = verify_plan(ctx, sol.assignment, sol.counted)
        if violations:  # không bao giờ trả phương án sai quy chế
            log.error("Phương án %s bị verifier loại: %s", r.strategy, [v.message for v in violations])
            result.warnings.append(f"Phương án {r.strategy.value} bị loại do không qua bộ kiểm chứng.")
            continue
        plan = build_plan(ctx, r.strategy, sol, explain=explain)
        plan.duplicate_of = dup.get(r.strategy)
        if plan.duplicate_of:
            plan.duplicate_of = plan.duplicate_of.lower()
        plans.append(plan)
    timings["explain"] = int((time.perf_counter() - t0) * 1000)
    if not plans:
        return _infeasible(result, ds, profile, reg, prefs, spec, [], timings, t0)
    result.plans = plans
    result.comparison = compare(plans)
    result.timings_ms = timings
    return result


def _infeasible(result, ds, profile, reg, prefs, spec, pre: list[Issue], timings, t0) -> PlanResult:
    result.status = "INFEASIBLE"
    result.infeasibility = explain_infeasibility(ds, profile, reg, prefs, spec, pre)
    timings["mus"] = int((time.perf_counter() - t0) * 1000)
    result.timings_ms = timings
    return result


def compare(plans: list[Plan]) -> Comparison:
    rows = [
        ComparisonRow(
            plan_id=p.id, strategy=p.strategy, title=p.title, metrics=p.metrics, duplicate_of=p.duplicate_of
        )
        for p in plans
    ]
    dist = {a.id: {b.id: plan_distance(a, b) for b in plans} for a in plans}
    return Comparison(rows=rows, distances=dist)


def context_for(
    ds: Dataset, profile: StudentProfile, regulation_id: str | None = None, prefs: Preferences | None = None
) -> PlanningContext:
    prefs = prefs or profile.preferences
    spec, _ = resolve_specialization(ds, profile, prefs, regulation_id)
    return build_context(ds, profile, regulation_id, prefs, spec=spec)
