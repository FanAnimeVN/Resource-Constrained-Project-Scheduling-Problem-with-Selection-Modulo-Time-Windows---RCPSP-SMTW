"""Mỗi ràng buộc cứng có ít nhất một kiểm thử trên dataset nhỏ."""

from helpers import block, mini_dataset, student

from curriculum_planner.analysis.context import build_context
from curriculum_planner.domain.models import AcademicRecord, Preferences, Strategy, Term
from curriculum_planner.solver.engine import plan_for_student
from curriculum_planner.solver.strategies import solve_fast
from curriculum_planner.verify.plan_verifier import verify_plan

REG = {"min_credits_main": 6, "max_credits_main": 9, "max_credits_summer": 3, "max_main_terms": 8}


def fast(d, s, prefs=None):
    ctx = build_context(d, s, prefs=prefs)
    r = solve_fast(ctx)
    return ctx, (r.solution if r else None)


def test_hc04_prerequisite_order_and_hc10_offering():
    d = mini_dataset(
        [("A", 3, ["HK1"]), ("B", 3, ["HK2"]), ("C", 3), ("D", 3), ("E", 3)],
        [block("K", ["A", "B", "C", "D", "E"], 15, rule="ALL_MANDATORY")],
        deps=[("A", "B", "PREREQUISITE")],
        total=15,
        regulation=REG,
    )
    ctx, sol = fast(d, student())
    a = sol.assignment
    assert a["A"] < a["B"]
    assert ctx.calendar.terms[a["A"]].kind.value == "HK1"
    assert ctx.calendar.terms[a["B"]].kind.value == "HK2"
    assert verify_plan(ctx, a, sol.counted) == []


def test_hc06_corequisite_same_term_allowed():
    d = mini_dataset(
        [("A", 3), ("B", 3)],
        [block("K", ["A", "B"], 6, rule="ALL_MANDATORY")],
        deps=[("A", "B", "CO_REQUISITE")],
        total=6,
        regulation=REG,
    )
    _, sol = fast(d, student())
    assert sol.assignment["A"] == sol.assignment["B"] == 0


def test_hc07_mutually_exclusive_never_both():
    d = mini_dataset(
        [("A", 3), ("B", 3), ("C", 3)],
        [block("K", ["A", "B", "C"], 6)],
        deps=[("A", "B", "MUTUALLY_EXCLUSIVE")],
        total=6,
        regulation=REG,
    )
    _, sol = fast(d, student())
    assert not ({"A", "B"} <= set(sol.assignment))
    assert "C" in sol.assignment


def test_hc08_load_bounds_and_final_term_exemption():
    """Trường hợp biên 4.1.4: kỳ cuối ít tín chỉ được miễn mức sàn."""
    d = mini_dataset(
        [(f"C{i}", 3) for i in range(7)],
        [block("K", [f"C{i}" for i in range(7)], 21, rule="ALL_MANDATORY")],
        total=21,
        regulation=REG,
    )
    ctx, sol = fast(d, student())
    loads = {}
    for _c, t in sol.assignment.items():
        loads[t] = loads.get(t, 0) + 3
    grad = max(loads)
    assert all(6 <= v <= 9 for t, v in loads.items() if t != grad)
    assert loads[grad] == 3  # 21 = 9 + 9 + 3: kỳ cuối 3 TC < sàn 6 vẫn hợp lệ


def test_hc09_summer_only_when_enabled():
    d = mini_dataset(
        [("A", 3, ["HK1", "HK2", "HE"]), ("B", 3), ("C", 3), ("D", 3)],
        [block("K", ["A", "B", "C", "D"], 12, rule="ALL_MANDATORY")],
        total=12,
        regulation=REG,
    )
    ctx, sol = fast(d, student())
    assert all(ctx.calendar.is_main(t) for t in sol.assignment.values())
    assert all(t.is_main for t in ctx.calendar.terms)
    ctx2, sol2 = fast(d, student(), Preferences(summer_enabled=True))
    assert any(not t.is_main for t in ctx2.calendar.terms)
    for t in range(len(ctx2.calendar.terms)):
        if not ctx2.calendar.is_main(t):
            assert sum(3 for c, tt in sol2.assignment.items() if tt == t) <= 3
    assert verify_plan(ctx2, sol2.assignment, sol2.counted) == []


def test_hc11_deadline_and_hc02_passed_not_rescheduled():
    d = mini_dataset(
        [("A", 3), ("B", 3), ("C", 3)],
        [block("K", ["A", "B", "C"], 9, rule="ALL_MANDATORY")],
        total=9,
        regulation=REG,
    )
    s = student(records=[AcademicRecord(course="A", status="PASSED", grade=8)])
    ctx, sol = fast(d, s)
    assert "A" not in sol.assignment
    assert sol.counted["A"] == "K"
    assert max(sol.assignment.values()) <= ctx.calendar.deadline_index


def test_hc03_min_credits_with_surplus_and_exact_rule():
    """Trường hợp biên 4.1.3: nhóm cần 6 TC, mọi môn 4 TC ⇒ phải học 8 TC (dư 2)."""
    courses = [("M", 4), ("E1", 4), ("E2", 4), ("E3", 4)]
    blocks = [block("BB", ["M"], 4, rule="ALL_MANDATORY"), block("TC", ["E1", "E2", "E3"], 6)]
    d = mini_dataset(courses, blocks, total=10, regulation=REG)
    res = plan_for_student(d, student(), strategies=[Strategy.FAST_TRACK], explain=False)
    assert res.status == "OK"
    plan = res.plans[0]
    assert plan.metrics.total_credits == 12 and plan.metrics.surplus_credits == 2
    d_exact = mini_dataset(courses, blocks, total=10, credit_rule="exact", regulation=REG)
    res2 = plan_for_student(d_exact, student(), strategies=[Strategy.FAST_TRACK], explain=False)
    assert res2.status == "INFEASIBLE"


def test_course_conditions_accumulated_and_final_term():
    d = mini_dataset(
        [("A", 3), ("B", 3), ("C", 3), ("D", 3), ("T", 3)],
        [block("K", ["A", "B", "C", "D", "T"], 15, rule="ALL_MANDATORY")],
        total=15,
        regulation=REG,
        course_extra={"T": {"min_accumulated_credits": 9, "final_term_only": True}},
    )
    ctx, sol = fast(d, student())
    a = sol.assignment
    assert a["T"] == max(a.values())
    before = sum(3 for c, t in a.items() if t < a["T"])
    assert before >= 9


def test_pinned_and_excluded_preferences():
    d = mini_dataset(
        [("A", 3), ("B", 3), ("E1", 3), ("E2", 3)],
        [block("BB", ["A", "B"], 6, rule="ALL_MANDATORY"), block("TC", ["E1", "E2"], 3)],
        total=9,
        regulation=REG,
    )
    prefs = Preferences(pinned=[{"course": "B", "term": Term(year=2026, kind="HK2")}], excluded=["E1"])
    ctx, sol = fast(d, student(), prefs)
    assert ctx.calendar.terms[sol.assignment["B"]] == Term(year=2026, kind="HK2")
    assert "E1" not in sol.assignment and "E2" in sol.assignment
    assert verify_plan(ctx, sol.assignment, sol.counted) == []
