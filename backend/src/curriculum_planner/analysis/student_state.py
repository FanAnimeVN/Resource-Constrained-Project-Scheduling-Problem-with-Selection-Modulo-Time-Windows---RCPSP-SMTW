"""Chuẩn hóa hồ sơ sinh viên: quy đổi tương đương, tập môn đã đạt / đã học, GPA."""

from __future__ import annotations

from dataclasses import dataclass, field

from curriculum_planner.data.loader import Dataset
from curriculum_planner.domain.models import Preferences, RecordStatus, StudentProfile


@dataclass
class StudentState:
    profile: StudentProfile
    satisfied: set[str]  # đã đạt / miễn / (đang học, nếu giả định đạt) – mã gốc
    attempted: set[str]  # satisfied ∪ đã từng học (kể cả rớt)
    failed: set[str]  # đã rớt và chưa đạt lại
    grades: dict[str, float]  # điểm cao nhất theo mã gốc
    gpa: float | None
    passed_credits: int  # tổng TC các môn đã thỏa (thuộc danh mục)
    mapped: dict[str, str] = field(default_factory=dict)  # mã cũ → mã gốc đã áp dụng
    outside: list[str] = field(default_factory=list)  # môn đã học nhưng không thuộc CTĐT
    warnings: list[str] = field(default_factory=list)

    def prereq_ok(self, course: str, min_grade: float | None) -> bool:
        if course not in self.satisfied:
            return False
        if min_grade is None:
            return True
        g = self.grades.get(course)
        return g is None or g >= min_grade


def build_state(ds: Dataset, profile: StudentProfile, prefs: Preferences | None = None) -> StudentState:
    prefs = prefs or profile.preferences
    eq = ds.equivalence_map
    satisfied: set[str] = set()
    attempted: set[str] = set()
    failed_raw: set[str] = set()
    grades: dict[str, float] = {}
    mapped: dict[str, str] = {}
    outside: list[str] = []
    warnings: list[str] = []
    graded_credits = 0.0
    graded_points = 0.0

    for r in profile.records:
        cid = r.course
        if cid not in ds.courses and cid in eq:
            mapped[cid] = eq[cid]
            cid = eq[cid]
        if cid not in ds.courses:
            outside.append(r.course)
            continue
        attempted.add(cid)
        if r.status in (RecordStatus.PASSED, RecordStatus.EXEMPTED):
            satisfied.add(cid)
            if r.grade is not None:
                grades[cid] = max(grades.get(cid, 0.0), r.grade)
        elif r.status == RecordStatus.IN_PROGRESS:
            if prefs.assume_in_progress_pass:
                satisfied.add(cid)
        elif r.status == RecordStatus.FAILED:
            failed_raw.add(cid)
        if r.grade is not None and r.status in (RecordStatus.PASSED, RecordStatus.FAILED):
            w = ds.courses[cid].credits
            graded_credits += w
            graded_points += w * r.grade

    if mapped:
        pairs = ", ".join(f"{k} → {v}" for k, v in sorted(mapped.items()))
        warnings.append(f"Đã quy đổi môn tương đương: {pairs}.")
    if outside:
        warnings.append(
            "Các môn sau không thuộc CTĐT nên không được tính vào tốt nghiệp: "
            + ", ".join(sorted(outside))
            + "."
        )
    gpa = round(graded_points / graded_credits, 2) if graded_credits else None
    passed_credits = sum(
        ds.courses[c].credits
        for c in satisfied
        if ds.courses[c].counts_toward_total and c in ds.course_leaf_blocks
    )
    return StudentState(
        profile=profile,
        satisfied=satisfied,
        attempted=attempted,
        failed=failed_raw - satisfied,
        grades=grades,
        gpa=gpa,
        passed_credits=passed_credits,
        mapped=mapped,
        outside=outside,
        warnings=warnings,
    )
