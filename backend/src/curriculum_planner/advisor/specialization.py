"""Tư vấn chọn chuyên ngành cá nhân hóa, minh bạch và gắn với bộ tối ưu.

Điểm mỗi chuyên ngành = tổng có trọng số của 4 thành phần (0..1):
- A học lực: điểm các môn chỉ báo, co về GPA chung khi ít dữ liệu (shrinkage);
- I sở thích: cosine(vector sở thích, hồ sơ chủ đề của chuyên ngành);
- C nghề nghiệp: tỉ lệ mục tiêu nghề của SV thuộc chuyên ngành;
- P tiến độ: chạy thử (what-if) bộ tối ưu để biết kỳ tốt nghiệp sớm nhất nếu chọn chuyên ngành đó.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from curriculum_planner.analysis.context import build_context
from curriculum_planner.analysis.prechecks import run_prechecks
from curriculum_planner.analysis.student_state import build_state
from curriculum_planner.data.loader import Dataset
from curriculum_planner.domain.models import Preferences, StudentProfile
from curriculum_planner.solver.strategies import solve_fast

SHRINK_M = 2.0


class ScoreComponents(BaseModel):
    academic: float
    interest: float
    career: float
    progress: float


class SpecializationScore(BaseModel):
    rank: int = 0
    specialization: str
    name: str
    description: str = ""
    score: float
    components: ScoreComponents
    confidence: str
    feasible: bool
    graduation_term: str | None = None
    graduation_index: int | None = None
    terms_vs_best: int = 0
    reused_credits: int = 0
    reasons: list[str] = Field(default_factory=list)


class SpecializationAdvice(BaseModel):
    student_id: str
    weights: dict[str, float]
    ranking: list[SpecializationScore]
    top: str | None
    stable: bool
    stability_note: str
    gpa: float | None


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _normalize(weights: dict[str, float]) -> dict[str, float]:
    s = sum(max(0.0, v) for v in weights.values()) or 1.0
    return {k: max(0.0, v) / s for k, v in weights.items()}


def recommend_specializations(
    ds: Dataset,
    profile: StudentProfile,
    regulation_id: str | None = None,
    prefs: Preferences | None = None,
    weights: dict[str, float] | None = None,
    run_progress: bool = True,
    time_limit: float = 2.0,
) -> SpecializationAdvice:
    if ds.advisor is None or not ds.curriculum.specializations:
        return SpecializationAdvice(
            student_id=profile.id, weights={}, ranking=[], top=None, stable=True, stability_note="", gpa=None
        )
    adv = ds.advisor
    prefs = prefs or profile.preferences
    state = build_state(ds, profile, prefs)
    w = _normalize(weights or adv.default_weights)
    gpa_norm = (state.gpa / 10) if state.gpa is not None else 0.5
    interests = {k: (v - 1) / 4 for k, v in profile.interests.items()}

    raw: list[dict] = []
    for spec in ds.curriculum.specializations:
        sp = adv.specializations.get(spec.id)
        if sp is None:
            continue
        reasons: list[str] = []
        # A – học lực
        num = den = 0.0
        graded = []
        for cid, wt in sp.indicator_courses.items():
            g = state.grades.get(cid)
            if g is not None:
                num += wt * g / 10
                den += wt
                graded.append((cid, g, wt))
        academic = (num + SHRINK_M * gpa_norm) / (den + SHRINK_M) if den else gpa_norm
        confidence = "cao" if len(graded) >= 3 else "trung bình" if graded else "thấp"
        strong = sorted((x for x in graded if x[1] >= 7.5), key=lambda x: (-x[1] * x[2], x[0]))[:3]
        if strong:
            parts = ", ".join(f"{ds.courses[c].name} ({g:g})" for c, g, _ in strong)
            reasons.append(f"Điểm tốt ở các môn nền tảng của chuyên ngành: {parts}.")
        weak = [x for x in graded if x[1] < 5.5]
        if weak:
            parts = ", ".join(f"{ds.courses[c].name} ({g:g})" for c, g, _ in weak[:2])
            reasons.append(f"Cần cải thiện: {parts}.")
        if not graded:
            reasons.append("Chưa có điểm các môn chỉ báo nên điểm học lực lấy mức trung tính.")
        # I – sở thích
        if interests:
            interest = _cosine(interests, sp.topic_profile)
            matched = [
                adv.topics.get(t, t)
                for t, v in sorted(sp.topic_profile.items(), key=lambda kv: -kv[1])
                if v >= 0.6 and profile.interests.get(t, 0) >= 4
            ]
            if matched:
                reasons.append("Khớp sở thích: " + ", ".join(matched) + ".")
        else:
            interest = 0.5
        # C – nghề nghiệp
        if profile.career_goals:
            hit = [c for c in profile.career_goals if c in sp.careers]
            career = len(hit) / len(profile.career_goals)
            if hit:
                names = ", ".join(adv.careers[c].name if c in adv.careers else c for c in hit)
                reasons.append(f"Phù hợp mục tiêu nghề nghiệp: {names}.")
        else:
            career = 0.5
        # P – tiến độ (what-if)
        members = {bc.id for b in ds.blocks[spec.block_id].walk() for bc in b.courses}
        reused = sum(ds.courses[c].credits for c in members if c in state.satisfied)
        g_idx, g_term, feasible = None, None, True
        if run_progress:
            ctx = build_context(ds, profile, regulation_id, prefs, spec=spec.id)
            if run_prechecks(ctx):
                feasible = False
            else:
                r = solve_fast(ctx, time_limit=time_limit, stages=[("grad", "min"), ("summer", "min")])
                if r is None:
                    feasible = False
                else:
                    g_idx = max(r.solution.assignment.values()) if r.solution.assignment else 0
                    g_term = ctx.calendar.label(g_idx)
        raw.append(
            dict(
                spec=spec,
                academic=academic,
                interest=interest,
                career=career,
                reasons=reasons,
                confidence=confidence,
                g_idx=g_idx,
                g_term=g_term,
                feasible=feasible,
                reused=reused,
            )
        )

    feas = [r["g_idx"] for r in raw if r["feasible"] and r["g_idx"] is not None]
    gmin, gmax = (min(feas), max(feas)) if feas else (0, 0)
    for r in raw:
        if not r["feasible"]:
            r["progress"] = 0.0
            r["reasons"].append("Không thể hoàn thành chuyên ngành này trong thời gian đào tạo còn lại.")
        elif r["g_idx"] is None:
            r["progress"] = 0.5
        else:
            r["progress"] = 1.0 if gmax == gmin else 1 - (r["g_idx"] - gmin) / (gmax - gmin)
            extra = r["g_idx"] - gmin
            msg = f"Nếu chọn: tốt nghiệp sớm nhất {r['g_term']}"
            msg += f" (chậm hơn {extra} học kỳ so với lựa chọn nhanh nhất)." if extra > 0 else "."
            r["reasons"].append(msg)
        if r["reused"]:
            r["reasons"].append(f"Đã tích lũy {r['reused']} TC thuộc chuyên ngành này.")

    def scores(weights_: dict[str, float]) -> list[tuple[float, str]]:
        return sorted(
            (
                (
                    weights_.get("academic", 0) * r["academic"]
                    + weights_.get("interest", 0) * r["interest"]
                    + weights_.get("career", 0) * r["career"]
                    + weights_.get("progress", 0) * r["progress"],
                    r["spec"].id,
                )
                for r in raw
            ),
            key=lambda x: (-x[0], x[1]),
        )

    base = scores(w)
    by_id = {r["spec"].id: r for r in raw}
    ranking: list[SpecializationScore] = []
    for rank, (s, sid) in enumerate(base, start=1):
        r = by_id[sid]
        ranking.append(
            SpecializationScore(
                rank=rank,
                specialization=sid,
                name=r["spec"].name,
                description=r["spec"].description,
                score=round(s, 4),
                components=ScoreComponents(
                    academic=round(r["academic"], 3),
                    interest=round(r["interest"], 3),
                    career=round(r["career"], 3),
                    progress=round(r["progress"], 3),
                ),
                confidence=r["confidence"],
                feasible=r["feasible"],
                graduation_term=r["g_term"],
                graduation_index=r["g_idx"],
                terms_vs_best=(r["g_idx"] - gmin) if r["g_idx"] is not None else 0,
                reused_credits=r["reused"],
                reasons=r["reasons"],
            )
        )
    top = ranking[0].specialization if ranking else None
    stable = True
    for k in w:
        for d in (-0.1, 0.1):
            w2 = dict(w)
            w2[k] = max(0.0, w2[k] + d)
            if scores(_normalize(w2))[0][1] != top:
                stable = False
    note = (
        "Thứ hạng đầu không đổi khi thay đổi mỗi trọng số ±0,1."
        if stable
        else "Thứ hạng đầu nhạy với trọng số: nên cân nhắc kỹ các lựa chọn đứng đầu."
    )
    return SpecializationAdvice(
        student_id=profile.id,
        weights=w,
        ranking=ranking,
        top=top,
        stable=stable,
        stability_note=note,
        gpa=state.gpa,
    )
