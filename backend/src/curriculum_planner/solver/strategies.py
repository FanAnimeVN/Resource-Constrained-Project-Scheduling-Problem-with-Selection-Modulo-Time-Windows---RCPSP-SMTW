"""Các chiến lược lập lộ trình = danh sách stage tối ưu theo thứ tự ưu tiên."""

from __future__ import annotations

import math
from dataclasses import dataclass

from curriculum_planner.analysis.context import PlanningContext, finalize_target
from curriculum_planner.domain.models import Strategy
from curriculum_planner.solver.model_builder import BuiltModel, add_safe_objective, build_model
from curriculum_planner.solver.runner import Solution, StageSolver

FAST_STAGES = [("grad", "min"), ("summer", "min"), ("credits", "min"), ("front", "min")]
BALANCED_STAGES = [("summer", "min"), ("credits", "min"), ("maxload", "min"), ("sq", "min"), ("peak", "min")]
RISK_STAGES = [("credits", "min"), ("safe", "max"), ("early", "min"), ("sq", "min")]
FOCUS_STAGES = [("credits", "min"), ("pref", "max"), ("sq", "min")]
PERSONALIZED_STAGES = [("credits", "min"), ("compromise", "min"), ("front", "min")]


@dataclass
class StrategyResult:
    strategy: Strategy
    solution: Solution
    solver: StageSolver


# ---- đánh giá mục tiêu trực tiếp từ phân bổ (dùng cho payoff & metrics) ------


def term_loads(ctx: PlanningContext, assignment: dict[str, int]) -> list[int]:
    loads = [0] * len(ctx.calendar.terms)
    for c, t in assignment.items():
        loads[t] += ctx.credits(c)
    return loads


def evaluate(ctx: PlanningContext, assignment: dict[str, int]) -> dict[str, float]:
    loads = term_loads(ctx, assignment)
    grad = max(assignment.values()) if assignment else -1
    main = [loads[t] for t in range(grad + 1) if ctx.calendar.is_main(t)]
    std = math.sqrt(sum((v - sum(main) / len(main)) ** 2 for v in main) / len(main)) if main else 0.0
    safe = sum(ctx.risk.get(c, 1) for c, t in assignment.items() if c in ctx.mandatory and ctx.safe(c, t))
    pref = sum(ctx.pref.get(c, 0) * ctx.credits(c) for c in assignment if c not in ctx.mandatory)
    return {
        "grad": grad,
        "maxload": max(main) if main else 0,
        "sq": sum(v * v for v in main),
        "std": std,
        "safe": safe,
        "pref": pref,
        "credits": sum(ctx.credits(c) for c in assignment),
    }


# ---- từng chiến lược ---------------------------------------------------------


def _new(ctx: PlanningContext, time_limit: float | None) -> tuple[BuiltModel, StageSolver]:
    b = build_model(ctx, "optimize")
    if ctx.safe_ls:
        add_safe_objective(b)
    return b, StageSolver(b, time_limit=time_limit)


def solve_fast(ctx: PlanningContext, time_limit: float | None = None, stages=None) -> StrategyResult | None:
    b, s = _new(ctx, time_limit)
    sol = s.run(stages or FAST_STAGES)
    return StrategyResult(Strategy.FAST_TRACK, sol, s) if sol else None


def solve_balanced(ctx: PlanningContext, time_limit: float | None = None) -> StrategyResult | None:
    """Cân bằng: tốt nghiệp không muộn hơn g_target; giảm tải đỉnh rồi giảm tổng bình phương tải (≈ phương sai)."""
    return _bounded(ctx, BALANCED_STAGES, Strategy.BALANCED, time_limit)


def _bounded(
    ctx: PlanningContext, stages, strategy: Strategy, time_limit: float | None
) -> StrategyResult | None:
    b, s = _new(ctx, time_limit)
    b.model.add(b.grad <= ctx.target_index)
    sol = s.run(stages)
    return StrategyResult(strategy, sol, s) if sol else None


def solve_risk(ctx: PlanningContext, time_limit: float | None = None) -> StrategyResult | None:
    return _bounded(ctx, RISK_STAGES, Strategy.RISK_AVERSE, time_limit)


def solve_focus(ctx: PlanningContext, time_limit: float | None = None) -> StrategyResult | None:
    return _bounded(ctx, FOCUS_STAGES, Strategy.SPECIALIZATION_FOCUS, time_limit)


def solve_personalized(
    ctx: PlanningContext, base: list[StrategyResult], time_limit: float | None = None
) -> StrategyResult | None:
    """Compromise programming: chuẩn hóa mục tiêu theo điểm lý tưởng/tệ nhất từ các phương án chiến lược."""
    w = ctx.prefs.objective_weights
    alpha = {"grad": w.fast, "maxload": w.balance, "safe": w.risk, "pref": w.interest}
    sense = {"grad": 1, "maxload": 1, "safe": -1, "pref": -1}  # +1: càng nhỏ càng tốt
    vals = [evaluate(ctx, r.solution.assignment) for r in base]
    b, s = _new(ctx, time_limit)
    b.model.add(b.grad <= ctx.target_index)
    obj = 0
    for k, a in alpha.items():
        if a <= 0 or k not in b.objectives:
            continue
        signed = [sense[k] * v[k] for v in vals]
        ideal, nadir = min(signed), max(signed)
        if nadir - ideal <= 0:
            continue
        coef = max(1, round(1000 * a / (nadir - ideal)))
        obj = obj + coef * sense[k] * b.objectives[k]
    if isinstance(obj, int):
        b.objectives["compromise"] = b.objectives["grad"]
    else:
        b.objectives["compromise"] = obj
    sol = s.run(PERSONALIZED_STAGES)
    return StrategyResult(Strategy.PERSONALIZED, sol, s) if sol else None


def solve_all(
    ctx: PlanningContext,
    strategies: list[Strategy] | None = None,
    time_limit: float | None = None,
) -> tuple[list[StrategyResult], dict[Strategy, str | None]]:
    """Giải các chiến lược; trả về kết quả và nhãn trùng lặp (duplicate_of)."""
    wanted = list(strategies or list(Strategy))
    fast = solve_fast(ctx, time_limit)
    if fast is None:
        return [], {}
    g_fast = max(fast.solution.assignment.values()) if fast.solution.assignment else 0
    finalize_target(ctx, g_fast)
    # f_safe cần g_target nên cập nhật cho mô hình FAST đã dựng
    add_safe_objective(fast.solver.b)

    results: list[StrategyResult] = []
    dup: dict[Strategy, str | None] = {}
    plan = [
        (Strategy.FAST_TRACK, lambda: fast),
        (Strategy.BALANCED, lambda: solve_balanced(ctx, time_limit)),
        (Strategy.RISK_AVERSE, lambda: solve_risk(ctx, time_limit)),
        (Strategy.SPECIALIZATION_FOCUS, lambda: solve_focus(ctx, time_limit)),
    ]
    base: list[StrategyResult] = []
    for strat, fn in plan:
        need_for_personalized = Strategy.PERSONALIZED in wanted
        if strat not in wanted and not need_for_personalized:
            continue
        r = fn()
        if r is None:
            continue
        # đa dạng: nếu trùng hoàn toàn phương án trước thì tìm lời giải khác cùng giá trị tối ưu
        same = [p for p in base if p.solution.assignment == r.solution.assignment]
        if same:
            alt = r.solver.resolve_different_from([p.solution.assignment for p in base])
            if alt is not None:
                r.solution = alt
                dup[strat] = None
            else:
                dup[strat] = same[0].strategy.value
        base.append(r)
        if strat in wanted:
            results.append(r)
    if Strategy.PERSONALIZED in wanted and base:
        p = solve_personalized(ctx, base, time_limit)
        if p is not None:
            same = [r for r in base if r.solution.assignment == p.solution.assignment]
            dup[Strategy.PERSONALIZED] = same[0].strategy.value if same else None
            results.insert(0, p)
    return results, dup
