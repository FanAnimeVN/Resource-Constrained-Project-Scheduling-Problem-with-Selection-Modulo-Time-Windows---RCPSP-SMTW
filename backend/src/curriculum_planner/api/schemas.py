"""Kiểu dữ liệu vào/ra của REST API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from curriculum_planner.advisor.next_term import NextTermAdvice
from curriculum_planner.domain.models import (
    Course,
    Curriculum,
    Dependency,
    Offering,
    Plan,
    Preferences,
    Strategy,
    StudentProfile,
)
from curriculum_planner.solver.engine import PlanResult


class StudentRef(BaseModel):
    dataset: str = "hcmus_cntt_k2020"
    regulation: str | None = None
    student_id: str | None = Field(default=None, description="Mã SV mẫu trong dataset")
    student: StudentProfile | None = Field(
        default=None, description="Hồ sơ SV gửi trực tiếp (ưu tiên hơn student_id)"
    )
    preferences: Preferences | None = None


class PlanRequest(StudentRef):
    strategies: list[Strategy] | None = None
    explain: bool = True


class AdviceRequest(StudentRef):
    weights: dict[str, float] | None = None
    interests: dict[str, int] | None = None
    career_goals: list[str] | None = None


class NextTermRequest(StudentRef):
    strategy: Strategy = Strategy.PERSONALIZED


class NextTermResponse(BaseModel):
    status: str
    advice: NextTermAdvice | None = None
    plan_result: PlanResult


class WhatIfRequest(StudentRef):
    plan: Plan
    course_id: str


class RegulationSummary(BaseModel):
    id: str
    name: str
    min_credits_main: int
    max_credits_main: int
    max_credits_summer: int
    max_main_terms: int


class StudentSummary(BaseModel):
    id: str
    name: str
    note: str
    cohort_year: int
    next_term: str


class DatasetSummary(BaseModel):
    id: str
    name: str
    total_credits_required: int
    courses: int
    dependencies: int
    regulations: list[RegulationSummary]
    students: list[StudentSummary]
    specializations: list[dict]
    topics: dict[str, str]
    careers: dict[str, str]


class CourseInfo(BaseModel):
    course: Course
    offering: Offering | None
    blocks: list[str]


class CatalogResponse(BaseModel):
    courses: list[CourseInfo]
    dependencies: list[Dependency]


class CurriculumResponse(BaseModel):
    curriculum: Curriculum
    block_kind: dict[str, str]
    block_specialization: dict[str, str | None]
