"""REST API (FastAPI). Chạy: `uvicorn curriculum_planner.api.app:app --reload`."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from curriculum_planner import __version__
from curriculum_planner.advisor.next_term import recommend_next_term
from curriculum_planner.advisor.specialization import SpecializationAdvice, recommend_specializations
from curriculum_planner.advisor.what_if import WhatIfResult, simulate_fail
from curriculum_planner.analysis.context import build_context
from curriculum_planner.api.schemas import (
    AdviceRequest,
    CatalogResponse,
    CourseInfo,
    CurriculumResponse,
    DatasetSummary,
    NextTermRequest,
    NextTermResponse,
    PlanRequest,
    RegulationSummary,
    StudentRef,
    StudentSummary,
    WhatIfRequest,
)
from curriculum_planner.data.loader import REPO_ROOT, Dataset, list_datasets, load_dataset
from curriculum_planner.domain.models import StudentProfile, ValidationReport
from curriculum_planner.solver.engine import PlanResult, cached_validation, plan_for_student

app = FastAPI(
    title="Hệ thống lập lộ trình học tập cá nhân hóa (RCPSP-SMTW)",
    version=__version__,
    description=(
        "API gợi ý lộ trình đăng ký tín chỉ tối ưu, giải trình từng môn, báo cáo xung đột khi vô nghiệm "
        "và tư vấn chọn chuyên ngành. Dữ liệu mẫu mô phỏng CTĐT CNTT 138 TC của ĐH KHTN – ĐHQG-HCM."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CPLAN_CORS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


def _dataset(ds_id: str) -> Dataset:
    try:
        return load_dataset(ds_id)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


def _student(ds: Dataset, ref: StudentRef) -> StudentProfile:
    if ref.student is not None:
        return ref.student
    if ref.student_id and ref.student_id in ds.students:
        return ds.students[ref.student_id]
    raise HTTPException(404, f"Không tìm thấy sinh viên '{ref.student_id}'")


def _regulation(ds: Dataset, reg_id: str | None):
    try:
        return ds.regulation(reg_id)
    except KeyError as e:
        raise HTTPException(404, str(e)) from e


def _prefs(ref: StudentRef, profile: StudentProfile):
    return ref.preferences or profile.preferences


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/api/datasets", response_model=list[DatasetSummary])
def datasets() -> list[DatasetSummary]:
    out = []
    for ds_id in list_datasets():
        ds = load_dataset(ds_id)
        adv = ds.advisor
        out.append(
            DatasetSummary(
                id=ds.id,
                name=ds.curriculum.name,
                total_credits_required=ds.curriculum.total_credits_required,
                courses=len(ds.courses),
                dependencies=len(ds.dependencies),
                regulations=[
                    RegulationSummary(
                        id=r.id,
                        name=r.name or r.id,
                        min_credits_main=r.min_credits_main,
                        max_credits_main=r.max_credits_main,
                        max_credits_summer=r.max_credits_summer,
                        max_main_terms=r.max_main_terms,
                    )
                    for r in ds.regulations.values()
                ],
                students=[
                    StudentSummary(
                        id=s.id,
                        name=s.name,
                        note=s.note,
                        cohort_year=s.cohort_year,
                        next_term=s.next_term.label,
                    )
                    for s in ds.students.values()
                ],
                specializations=[s.model_dump() for s in ds.curriculum.specializations],
                topics=adv.topics if adv else {},
                careers={k: v.name for k, v in adv.careers.items()} if adv else {},
            )
        )
    return out


@app.get("/api/datasets/{ds_id}/curriculum", response_model=CurriculumResponse)
def curriculum(ds_id: str) -> CurriculumResponse:
    ds = _dataset(ds_id)
    return CurriculumResponse(
        curriculum=ds.curriculum, block_kind=ds.block_kind, block_specialization=ds.block_specialization
    )


@app.get("/api/datasets/{ds_id}/courses", response_model=CatalogResponse)
def courses(ds_id: str) -> CatalogResponse:
    ds = _dataset(ds_id)
    return CatalogResponse(
        courses=[
            CourseInfo(course=c, offering=ds.offerings.get(c.id), blocks=ds.course_leaf_blocks.get(c.id, []))
            for c in ds.courses.values()
        ],
        dependencies=ds.dependencies,
    )


@app.get("/api/datasets/{ds_id}/validation", response_model=ValidationReport)
def validation(ds_id: str) -> ValidationReport:
    return cached_validation(_dataset(ds_id))


@app.get("/api/datasets/{ds_id}/students", response_model=list[StudentProfile])
def students(ds_id: str) -> list[StudentProfile]:
    return list(_dataset(ds_id).students.values())


@app.get("/api/datasets/{ds_id}/students/{student_id}", response_model=StudentProfile)
def student(ds_id: str, student_id: str) -> StudentProfile:
    ds = _dataset(ds_id)
    if student_id not in ds.students:
        raise HTTPException(404, f"Không tìm thấy sinh viên '{student_id}'")
    return ds.students[student_id]


@app.post("/api/plans", response_model=PlanResult)
def plans(req: PlanRequest):
    ds = _dataset(req.dataset)
    profile = _student(ds, req)
    res = plan_for_student(
        ds,
        profile,
        prefs=_prefs(req, profile),
        strategies=req.strategies,
        explain=req.explain,
        regulation=_regulation(ds, req.regulation),
    )
    if res.status == "DATA_ERROR":
        return JSONResponse(status_code=422, content=res.model_dump(mode="json"))
    return res


@app.post("/api/advisor/specializations", response_model=SpecializationAdvice)
def advisor(req: AdviceRequest) -> SpecializationAdvice:
    ds = _dataset(req.dataset)
    profile = _student(ds, req)
    update = {}
    if req.interests is not None:
        update["interests"] = req.interests
    if req.career_goals is not None:
        update["career_goals"] = req.career_goals
    if update:
        profile = profile.model_copy(update=update)
    reg = _regulation(ds, req.regulation)
    return recommend_specializations(ds, profile, reg.id, _prefs(req, profile), req.weights)


@app.post("/api/recommendations/next-term", response_model=NextTermResponse)
def next_term(req: NextTermRequest) -> NextTermResponse:
    ds = _dataset(req.dataset)
    profile = _student(ds, req)
    prefs = _prefs(req, profile)
    reg = _regulation(ds, req.regulation)
    res = plan_for_student(ds, profile, prefs=prefs, strategies=[req.strategy], explain=False, regulation=reg)
    if res.status != "OK" or not res.plans:
        return NextTermResponse(status=res.status, plan_result=res)
    plan = next((p for p in res.plans if p.strategy == req.strategy), res.plans[0])
    ctx = build_context(ds, profile, prefs=prefs, spec=res.specialization, regulation=reg)
    return NextTermResponse(status="OK", advice=recommend_next_term(ctx, plan), plan_result=res)


@app.post("/api/what-if/fail", response_model=WhatIfResult)
def what_if(req: WhatIfRequest) -> WhatIfResult:
    ds = _dataset(req.dataset)
    profile = _student(ds, req)
    try:
        return simulate_fail(ds, profile, req.plan, req.course_id, _prefs(req, profile), req.regulation)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


# ---- phục vụ giao diện đã build (một tiến trình cho cả API + web) ----
_DIST = Path(os.environ.get("CPLAN_WEB_DIST", REPO_ROOT / "frontend" / "dist"))
if _DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = _DIST / path
        if path and f.is_file():
            return FileResponse(f)
        return FileResponse(_DIST / "index.html")
