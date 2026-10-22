"""Dựng nhanh dataset nhỏ trong bộ nhớ cho kiểm thử."""

from __future__ import annotations

from curriculum_planner.data.loader import Dataset
from curriculum_planner.domain.models import (
    Course,
    Curriculum,
    Dependency,
    KnowledgeBlock,
    Offering,
    Regulation,
    StudentProfile,
    Term,
)


def mini_dataset(
    courses: list[tuple],  # (id, credits) | (id, credits, terms) | (id, credits, terms, name)
    blocks: list[dict],
    deps: list[tuple] = (),  # (source, target, type)
    total: int = 30,
    credit_rule: str = "at_least",
    standard_main_terms: int = 8,
    regulation: dict | None = None,
    course_extra: dict | None = None,
) -> Dataset:
    cs, offs = {}, {}
    for spec in courses:
        cid, cr = spec[0], spec[1]
        terms = spec[2] if len(spec) > 2 else ["HK1", "HK2"]
        name = spec[3] if len(spec) > 3 else cid
        extra = (course_extra or {}).get(cid, {})
        cs[cid] = Course(id=cid, name=name, credits=cr, **extra)
        offs[cid] = Offering(course=cid, terms=terms)
    reg = Regulation(id="default", **(regulation or {}))
    return Dataset(
        id="mini",
        courses=cs,
        dependencies=[Dependency(source=a, target=b, type=t) for a, b, t in deps],
        offerings=offs,
        curriculum=Curriculum(
            id="MINI",
            name="Mini",
            total_credits_required=total,
            credit_rule=credit_rule,
            standard_main_terms=standard_main_terms,
            blocks=[KnowledgeBlock.model_validate(b) for b in blocks],
        ),
        regulations={"default": reg},
    )


def student(cohort=2026, year=2026, kind="HK1", records=(), **kw) -> StudentProfile:
    return StudentProfile(
        id=kw.pop("id", "s"),
        name="Sinh viên thử",
        cohort_year=cohort,
        curriculum_id="MINI",
        next_term=Term(year=year, kind=kind),
        records=list(records),
        **kw,
    )


def block(id, courses, required, rule="MIN_CREDITS", mandatory=()):
    return {
        "id": id,
        "name": id,
        "rule": rule,
        "required_credits": required,
        "courses": [{"id": c, "mandatory": c in mandatory} for c in courses],
    }
