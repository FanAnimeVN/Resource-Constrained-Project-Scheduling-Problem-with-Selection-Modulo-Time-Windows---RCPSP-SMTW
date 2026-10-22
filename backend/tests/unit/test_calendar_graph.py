from helpers import block, mini_dataset, student

from curriculum_planner.analysis.calendar import build_calendar, main_term_number
from curriculum_planner.analysis.context import build_context
from curriculum_planner.domain.models import Term, TermKind


def test_calendar_deadline_and_summer():
    cal = build_calendar(2024, Term(year=2026, kind=TermKind.HK2), 12, 8, summer_enabled=True)
    assert cal.terms[0].label == "HK2 2026–2027"
    assert cal.terms[1].label == "Hè 2027"
    assert cal.deadline_term == Term(year=2029, kind=TermKind.HE)
    assert cal.terms[cal.standard_index] == Term(year=2027, kind=TermKind.HK2)
    assert main_term_number(2024, Term(year=2026, kind=TermKind.HK2)) == 6


def test_calendar_without_summer_skips_summer_start():
    cal = build_calendar(2024, Term(year=2026, kind=TermKind.HE), 12, 8, summer_enabled=False)
    assert cal.terms[0] == Term(year=2027, kind=TermKind.HK1)
    assert all(t.is_main for t in cal.terms)


def test_offering_phase_shift_delays_successor_one_year():
    """Trường hợp biên 4.1.2: A tiên quyết của B, cả hai chỉ mở HK1 ⇒ B sớm nhất là HK1 năm sau."""
    d = mini_dataset(
        [("A", 3, ["HK1"]), ("B", 3, ["HK1"]), ("F", 14)],
        [block("K", ["A", "B", "F"], 20, rule="ALL_MANDATORY")],
        deps=[("A", "B", "PREREQUISITE")],
        total=20,
    )
    ctx = build_context(d, student())
    assert ctx.calendar.label(ctx.es["A"]) == "HK1 2026–2027"
    assert ctx.calendar.label(ctx.es["B"]) == "HK1 2027–2028"


def test_failed_pre_course_still_counts_as_attempted():
    """Học trước: đã HỌC (kể cả rớt) là đủ; tiên quyết: phải ĐẠT."""
    from curriculum_planner.domain.models import AcademicRecord

    d = mini_dataset(
        [("A", 3), ("B", 3), ("C", 3)],
        [block("K", ["A", "B", "C"], 9, rule="ALL_MANDATORY")],
        deps=[("A", "B", "PRE_COURSE"), ("A", "C", "PREREQUISITE")],
        total=9,
    )
    s = student(records=[AcademicRecord(course="A", status="FAILED", grade=3.0)])
    ctx = build_context(d, s)
    dep_b, dep_c = d.dependencies
    assert ctx.dep_satisfied(dep_b) is True
    assert ctx.dep_satisfied(dep_c) is False
    assert "A" in ctx.candidates  # vẫn phải học lại A (bắt buộc)
