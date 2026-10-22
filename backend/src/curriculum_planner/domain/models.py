"""Mô hình miền (domain) của hệ thống.

Toàn bộ dữ liệu danh mục, quy chế, hồ sơ sinh viên và kết quả lộ trình đều được mô tả ở đây
bằng Pydantic v2. Các module thuật toán chỉ đọc những đối tượng này, không đọc file trực tiếp.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Thời gian
# ---------------------------------------------------------------------------


class TermKind(StrEnum):
    HK1 = "HK1"
    HK2 = "HK2"
    HE = "HE"


TERM_KIND_ORDER = {TermKind.HK1: 0, TermKind.HK2: 1, TermKind.HE: 2}


class Term(BaseModel):
    """Một học kỳ: năm bắt đầu của năm học + loại kỳ. Ví dụ (2026, HK1) = HK1 2026–2027."""

    model_config = ConfigDict(frozen=True)

    year: int
    kind: TermKind

    @property
    def is_main(self) -> bool:
        return self.kind != TermKind.HE

    @property
    def sort_key(self) -> tuple[int, int]:
        return (self.year, TERM_KIND_ORDER[self.kind])

    @property
    def label(self) -> str:
        if self.kind == TermKind.HE:
            return f"Hè {self.year + 1}"
        return f"{self.kind.value} {self.year}–{self.year + 1}"

    def next(self, include_summer: bool = True) -> Term:
        if self.kind == TermKind.HK1:
            return Term(year=self.year, kind=TermKind.HK2)
        if self.kind == TermKind.HK2:
            if include_summer:
                return Term(year=self.year, kind=TermKind.HE)
            return Term(year=self.year + 1, kind=TermKind.HK1)
        return Term(year=self.year + 1, kind=TermKind.HK1)

    def __str__(self) -> str:  # pragma: no cover - tiện debug
        return self.label


# ---------------------------------------------------------------------------
# Danh mục học phần
# ---------------------------------------------------------------------------


class Course(BaseModel):
    id: str
    name: str
    credits: int = Field(gt=0)
    workload: int = Field(default=3, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True
    min_accumulated_credits: int | None = None
    final_term_only: bool = False
    min_gpa: float | None = None
    historical_fail_rate: float | None = Field(default=None, ge=0, le=1)
    counts_toward_total: bool = True
    source: str = "sample"


class DependencyType(StrEnum):
    PREREQUISITE = "PREREQUISITE"  # tiên quyết: phải ĐẠT
    PRE_COURSE = "PRE_COURSE"  # học trước: phải đã HỌC
    CO_REQUISITE = "CO_REQUISITE"  # song hành: trước hoặc cùng kỳ
    MUTUALLY_EXCLUSIVE = "MUTUALLY_EXCLUSIVE"  # loại trừ / thay thế


STRICT_DEPENDENCIES = {DependencyType.PREREQUISITE, DependencyType.PRE_COURSE}


class Dependency(BaseModel):
    source: str
    target: str
    type: DependencyType
    min_grade: float | None = None
    note: str = "sample"


_PATTERN_TERMS: dict[str, tuple[list[str], str | None]] = {
    "FALL_ONLY": (["HK1"], None),
    "SPRING_ONLY": (["HK2"], None),
    "EVERY_TERM": (["HK1", "HK2"], None),
    "SUMMER_ALLOWED": (["HK1", "HK2", "HE"], None),
    "ODD_YEARS_ONLY": (["HK1", "HK2"], "odd"),
    "EVEN_YEARS_ONLY": (["HK1", "HK2"], "even"),
}


class Offering(BaseModel):
    """Quy tắc mở môn. `year_parity` áp lên năm bắt đầu của năm học."""

    course: str
    terms: list[TermKind]
    year_parity: Literal["odd", "even"] | None = None

    @model_validator(mode="before")
    @classmethod
    def _accept_spec_enum(cls, data):  # nhận cả enum của đặc tả gốc
        if isinstance(data, dict) and "pattern" in data and "terms" not in data:
            terms, parity = _PATTERN_TERMS[data["pattern"]]
            data = {**data, "terms": terms, "year_parity": data.get("year_parity", parity)}
            data.pop("pattern")
        return data

    def is_offered(self, term: Term) -> bool:
        if term.kind not in self.terms:
            return False
        if self.year_parity == "odd" and term.year % 2 == 0:
            return False
        if self.year_parity == "even" and term.year % 2 == 1:
            return False
        return True

    @property
    def offers_per_year(self) -> float:
        main = sum(1 for k in self.terms if k != TermKind.HE)
        return main / (2 if self.year_parity else 1)


# ---------------------------------------------------------------------------
# Chương trình đào tạo & quy chế
# ---------------------------------------------------------------------------


class SelectionRule(StrEnum):
    ALL_MANDATORY = "ALL_MANDATORY"
    MIN_CREDITS = "MIN_CREDITS"
    PICK_K_OF_N = "PICK_K_OF_N"


class BlockCourse(BaseModel):
    id: str
    mandatory: bool = False


class KnowledgeBlock(BaseModel):
    id: str
    name: str
    rule: SelectionRule = SelectionRule.MIN_CREDITS
    required_credits: int = 0
    k: int | None = None
    specialization: str | None = None
    specialization_group: bool = False
    kind: Literal["general", "foundation", "major", "free", "graduation", "other"] = "other"
    children: list[KnowledgeBlock] = Field(default_factory=list)
    courses: list[BlockCourse] = Field(default_factory=list)

    @property
    def is_leaf(self) -> bool:
        return not self.children

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def leaves(self):
        for b in self.walk():
            if b.is_leaf:
                yield b

    def mandatory_ids(self) -> list[str]:
        if self.rule == SelectionRule.ALL_MANDATORY:
            return [c.id for c in self.courses]
        return [c.id for c in self.courses if c.mandatory]


class Specialization(BaseModel):
    id: str
    name: str
    block_id: str
    description: str = ""


class Curriculum(BaseModel):
    id: str
    name: str
    total_credits_required: int = 138
    credit_rule: Literal["at_least", "exact"] = "at_least"
    standard_main_terms: int = 8
    blocks: list[KnowledgeBlock]
    specializations: list[Specialization] = Field(default_factory=list)
    graduation_conditions: list[str] = Field(default_factory=list)

    def all_blocks(self) -> list[KnowledgeBlock]:
        out: list[KnowledgeBlock] = []
        for b in self.blocks:
            out.extend(b.walk())
        return out

    def leaf_blocks(self) -> list[KnowledgeBlock]:
        return [b for b in self.all_blocks() if b.is_leaf]


class LoadRule(BaseModel):
    when: str  # "academic_warning" | "gpa_at_least:8.0"
    min_credits_main: int | None = None
    max_credits_main: int | None = None


class Regulation(BaseModel):
    id: str
    name: str = ""
    min_credits_main: int = 14
    max_credits_main: int = 24
    max_credits_summer: int = 8
    final_term_min_exempt: bool = True
    max_main_terms: int = 12
    allow_empty_main_terms: bool = False
    allow_double_count_across_blocks: bool = False
    load_rules: list[LoadRule] = Field(default_factory=list)
    source: str = "sample"


class Equivalence(BaseModel):
    canonical: str
    equivalents: list[str]
    kind: Literal["EQUIVALENT", "SUBSTITUTE"] = "EQUIVALENT"


class CareerProfile(BaseModel):
    name: str
    topics: list[str] = Field(default_factory=list)


class SpecializationProfile(BaseModel):
    topic_profile: dict[str, float]
    indicator_courses: dict[str, float]
    careers: list[str] = Field(default_factory=list)


class AdvisorConfig(BaseModel):
    topics: dict[str, str]
    careers: dict[str, CareerProfile] = Field(default_factory=dict)
    specializations: dict[str, SpecializationProfile] = Field(default_factory=dict)
    default_weights: dict[str, float] = Field(
        default_factory=lambda: {"academic": 0.35, "interest": 0.30, "career": 0.15, "progress": 0.20}
    )


# ---------------------------------------------------------------------------
# Sinh viên
# ---------------------------------------------------------------------------


class RecordStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    EXEMPTED = "EXEMPTED"
    IN_PROGRESS = "IN_PROGRESS"


class AcademicRecord(BaseModel):
    course: str
    status: RecordStatus
    grade: float | None = Field(default=None, ge=0, le=10)
    term: Term | None = None


class PinnedCourse(BaseModel):
    course: str
    term: Term


class ObjectiveWeights(BaseModel):
    fast: float = 0.25
    balance: float = 0.35
    risk: float = 0.25
    interest: float = 0.15


class Preferences(BaseModel):
    summer_enabled: bool = False
    personal_max_credits: int | None = None
    target_graduation_term: Term | None = None
    specialization: str | None = None  # None/"auto" → dùng gợi ý của bộ tư vấn
    pinned: list[PinnedCourse] = Field(default_factory=list)
    excluded: list[str] = Field(default_factory=list)
    objective_weights: ObjectiveWeights = Field(default_factory=ObjectiveWeights)
    assume_in_progress_pass: bool = True


class StudentProfile(BaseModel):
    id: str
    name: str
    cohort_year: int
    curriculum_id: str
    next_term: Term
    records: list[AcademicRecord] = Field(default_factory=list)
    academic_warning: bool = False
    declared_specialization: str | None = None
    interests: dict[str, int] = Field(default_factory=dict)
    career_goals: list[str] = Field(default_factory=list)
    preferences: Preferences = Field(default_factory=Preferences)
    note: str = ""

    @field_validator("interests")
    @classmethod
    def _check_interests(cls, v: dict[str, int]) -> dict[str, int]:
        for topic, score in v.items():
            if not 1 <= score <= 5:
                raise ValueError(f"Điểm sở thích của '{topic}' phải trong 1..5")
        return v


# ---------------------------------------------------------------------------
# Kết quả
# ---------------------------------------------------------------------------


class Severity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"


class Issue(BaseModel):
    code: str
    severity: Severity = Severity.ERROR
    message: str
    courses: list[str] = Field(default_factory=list)
    terms: list[str] = Field(default_factory=list)


class ValidationReport(BaseModel):
    dataset: str
    issues: list[Issue] = Field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def ok(self) -> bool:
        return not self.errors


class Strategy(StrEnum):
    FAST_TRACK = "FAST_TRACK"
    BALANCED = "BALANCED"
    RISK_AVERSE = "RISK_AVERSE"
    SPECIALIZATION_FOCUS = "SPECIALIZATION_FOCUS"
    PERSONALIZED = "PERSONALIZED"


STRATEGY_TITLES = {
    Strategy.FAST_TRACK: "Tốt nghiệp sớm",
    Strategy.BALANCED: "Cân bằng tải",
    Strategy.RISK_AVERSE: "An toàn (giảm rủi ro)",
    Strategy.SPECIALIZATION_FOCUS: "Theo định hướng",
    Strategy.PERSONALIZED: "Đề xuất cho bạn",
}


class Reason(BaseModel):
    code: str
    message: str
    courses: list[str] = Field(default_factory=list)
    terms: list[str] = Field(default_factory=list)


class Explanation(BaseModel):
    selection_kind: Literal["MANDATORY", "ELECTIVE", "REQUIRED_AS_PREREQ", "OTHER"]
    selection: list[Reason] = Field(default_factory=list)
    timing: list[Reason] = Field(default_factory=list)
    earliest_term: str | None = None
    delayed_by_strategy: bool = False
    requires: list[Reason] = Field(default_factory=list)
    unlocks: list[str] = Field(default_factory=list)
    on_critical_path: bool = False
    risk_score: int = 0
    risk_factors: list[str] = Field(default_factory=list)
    retake_safe: bool | None = None
    retake_term: str | None = None


class ScheduledCourse(BaseModel):
    course_id: str
    name: str
    credits: int
    workload: int
    counted_block: str | None
    block_kind: str = "other"
    tags: list[str] = Field(default_factory=list)
    badges: list[str] = Field(default_factory=list)
    explanation: Explanation | None = None


class PlanTerm(BaseModel):
    index: int
    term: Term
    label: str
    is_main: bool
    credits: int
    workload: int
    min_credits: int | None
    max_credits: int
    courses: list[ScheduledCourse]


class BlockProgress(BaseModel):
    block_id: str
    name: str
    depth: int
    required: int
    passed_credits: int
    planned_credits: int


class PlanMetrics(BaseModel):
    graduation_term: str
    graduation_index: int
    main_terms_remaining: int
    total_main_terms: int
    planned_credits: int
    total_credits: int
    surplus_credits: int
    load_std: float
    load_max: int
    load_min: int
    peak_workload: int
    summers_used: int
    risk_coverage: float
    interest_score: float
    focus_ratio: float
    solver_status: str
    solve_ms: int


class Plan(BaseModel):
    id: str
    strategy: Strategy
    title: str
    specialization: str | None
    specialization_name: str | None = None
    terms: list[PlanTerm]
    passed_assignment: dict[str, str | None] = Field(default_factory=dict)
    block_progress: list[BlockProgress] = Field(default_factory=list)
    metrics: PlanMetrics
    highlights: list[str] = Field(default_factory=list)
    duplicate_of: str | None = None

    def assignment(self) -> dict[str, int]:
        return {c.course_id: t.index for t in self.terms for c in t.courses}

    def scheduled(self) -> list[tuple[PlanTerm, ScheduledCourse]]:
        return [(t, c) for t in self.terms for c in t.courses]


class Conflict(BaseModel):
    code: str
    message: str
    courses: list[str] = Field(default_factory=list)
    terms: list[str] = Field(default_factory=list)
    relaxable: bool = False


class Suggestion(BaseModel):
    code: str
    message: str
    graduation_term: str | None = None


class InfeasibilityReport(BaseModel):
    summary: str
    prechecks: list[Issue] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    minimal: bool = True
    suggestions: list[Suggestion] = Field(default_factory=list)


KnowledgeBlock.model_rebuild()
