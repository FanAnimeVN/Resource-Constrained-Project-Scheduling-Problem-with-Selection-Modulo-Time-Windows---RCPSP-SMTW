"""Property-based: solver ≡ duyệt vét cạn (qua verifier), mọi lời giải hợp lệ, MUS là tối thiểu."""

import itertools

from helpers import mini_dataset, student
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from ortools.sat.python import cp_model

from curriculum_planner.analysis.context import build_context
from curriculum_planner.solver.model_builder import build_model
from curriculum_planner.solver.mus import _check, find_mus
from curriculum_planner.solver.strategies import solve_fast
from curriculum_planner.verify.plan_verifier import verify_plan

TERMS = [["HK1"], ["HK2"], ["HK1", "HK2"]]
TYPES = ["PREREQUISITE", "PRE_COURSE", "CO_REQUISITE"]


@st.composite
def instances(draw):
    n = draw(st.integers(2, 4))
    ids = [f"C{i}" for i in range(n)]
    credits = [draw(st.integers(1, 4)) for _ in ids]
    courses = [(c, cr, draw(st.sampled_from(TERMS))) for c, cr in zip(ids, credits, strict=True)]
    deps = []
    for j in range(n):
        for i in range(j):
            if draw(st.integers(0, 3)) == 0:
                deps.append((ids[i], ids[j], draw(st.sampled_from(TYPES))))
    mandatory = [c for c in ids if draw(st.booleans())]
    req = draw(st.integers(1, sum(credits)))
    blocks = [
        {
            "id": "K",
            "name": "K",
            "rule": "MIN_CREDITS",
            "required_credits": req,
            "courses": [{"id": c, "mandatory": c in mandatory} for c in ids],
        }
    ]
    reg = {
        "min_credits_main": draw(st.integers(0, 4)),
        "max_credits_main": draw(st.integers(4, 8)),
        "max_main_terms": draw(st.integers(2, 4)),
    }
    return mini_dataset(courses, blocks, deps=deps, total=req, regulation=reg)


def brute_force_feasible(ctx) -> bool:
    ids = sorted(ctx.candidates)
    H = len(ctx.calendar.terms)
    for combo in itertools.product([None, *range(H)], repeat=len(ids)):
        a = {c: t for c, t in zip(ids, combo, strict=True) if t is not None}
        if not a:
            continue
        if not verify_plan(ctx, a, {c: "K" for c in a}):
            return True
    return False


@settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(instances())
def test_solver_matches_brute_force_and_verifier(d):
    ctx = build_context(d, student(cohort=2026))
    r = solve_fast(ctx, time_limit=5.0)
    if r is not None:
        assert verify_plan(ctx, r.solution.assignment, r.solution.counted) == []
    assert (r is not None) == brute_force_feasible(ctx)


@settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(instances())
def test_mus_is_minimal(d):
    ctx_opt = build_context(d, student(cohort=2026))
    if solve_fast(ctx_opt, time_limit=5.0) is not None:
        return
    ctx = build_context(d, student(cohort=2026), mode="explain")
    b = build_model(ctx, "explain")
    res = find_mus(b, budget_s=30)
    if res.feasible:  # vô nghiệm chỉ vì hạn chót cắt horizon ⇒ explain-mode vẫn phải thấy xung đột
        raise AssertionError("explain model phải vô nghiệm khi optimize model vô nghiệm")
    assert res.keys
    st_all, _ = _check(b, res.keys, 5.0)
    assert st_all == cp_model.INFEASIBLE
    if res.minimal:
        for k in res.keys:
            st_k, _ = _check(b, [x for x in res.keys if x != k], 5.0)
            assert st_k in (cp_model.OPTIMAL, cp_model.FEASIBLE)
