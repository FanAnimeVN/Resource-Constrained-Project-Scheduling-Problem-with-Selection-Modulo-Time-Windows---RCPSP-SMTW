"""Mô phỏng "nếu rớt môn X ở kỳ Y": lập lại lộ trình và đo độ trễ tốt nghiệp."""

from __future__ import annotations

from pydantic import BaseModel

from curriculum_planner.analysis.calendar import main_term_number
from curriculum_planner.data.loader import Dataset
from curriculum_planner.domain.models import (
    AcademicRecord,
    Plan,
    Preferences,
    RecordStatus,
    Strategy,
    StudentProfile,
)
from curriculum_planner.solver.engine import PlanResult, plan_for_student


class WhatIfResult(BaseModel):
    course_id: str
    course_name: str
    failed_term: str
    original_graduation: str
    status: str
    new_graduation: str | None = None
    delay_main_terms: int | None = None
    message: str
    result: PlanResult


def simulate_fail(
    ds: Dataset,
    profile: StudentProfile,
    plan: Plan,
    course_id: str,
    prefs: Preferences | None = None,
    regulation_id: str | None = None,
) -> WhatIfResult:
    prefs = (prefs or profile.preferences).model_copy(update={"specialization": plan.specialization})
    assignment = plan.assignment()
    if course_id not in assignment:
        raise ValueError(f"Môn {course_id} không có trong phương án {plan.id}")
    t = assignment[course_id]
    term = plan.terms[t].term
    records = list(profile.records)
    for pt in plan.terms[: t + 1]:
        for c in pt.courses:
            status = RecordStatus.FAILED if c.course_id == course_id else RecordStatus.PASSED
            grade = 3.0 if status == RecordStatus.FAILED else 7.0
            records.append(AcademicRecord(course=c.course_id, status=status, grade=grade, term=pt.term))
    new_profile = profile.model_copy(
        update={"records": records, "next_term": term.next(include_summer=prefs.summer_enabled)}
    )
    res = plan_for_student(
        ds,
        new_profile,
        regulation_id,
        prefs,
        strategies=[Strategy.FAST_TRACK, Strategy.PERSONALIZED],
        explain=True,
    )
    name = ds.courses[course_id].name
    orig = plan.terms[plan.metrics.graduation_index].term
    if res.status == "OK" and res.plans:
        best = min(res.plans, key=lambda p: p.metrics.graduation_index)
        new_term = best.terms[best.metrics.graduation_index].term
        delay = int(
            main_term_number(profile.cohort_year, new_term) - main_term_number(profile.cohort_year, orig)
        )
        delay = max(0, delay)
        if delay == 0:
            message = f"Nếu rớt {name} ở {term.label}, bạn vẫn có thể tốt nghiệp đúng {orig.label}."
        else:
            message = (
                f"Nếu rớt {name} ở {term.label}, tốt nghiệp sớm nhất lùi đến {new_term.label} "
                f"(chậm {delay} học kỳ chính)."
            )
        return WhatIfResult(
            course_id=course_id,
            course_name=name,
            failed_term=term.label,
            original_graduation=orig.label,
            status=res.status,
            new_graduation=new_term.label,
            delay_main_terms=delay,
            message=message,
            result=res,
        )
    return WhatIfResult(
        course_id=course_id,
        course_name=name,
        failed_term=term.label,
        original_graduation=orig.label,
        status=res.status,
        message=f"Nếu rớt {name} ở {term.label}, không còn lộ trình hợp lệ trước hạn tối đa.",
        result=res,
    )
