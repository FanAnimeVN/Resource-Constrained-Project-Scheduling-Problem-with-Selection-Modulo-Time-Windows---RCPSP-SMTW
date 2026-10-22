"""Gợi ý danh sách môn đăng ký cho học kỳ kế tiếp, kèm môn thay thế và cảnh báo."""

from __future__ import annotations

from pydantic import BaseModel, Field

from curriculum_planner.analysis.context import PlanningContext
from curriculum_planner.domain.models import DependencyType, Plan, TermKind


class CourseSuggestion(BaseModel):
    course_id: str
    name: str
    credits: int
    mandatory: bool
    block: str | None = None
    score: float = 0.0
    badges: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class NextTermAdvice(BaseModel):
    term: str
    plan_id: str
    recommended: list[CourseSuggestion]
    alternatives: list[CourseSuggestion]
    total_credits: int
    min_credits: int | None
    max_credits: int
    warnings: list[str] = Field(default_factory=list)


def _block_needs(ctx: PlanningContext) -> dict[str, int]:
    """TC còn thiếu của từng khối lá (chỉ tính môn đã đạt)."""
    ds = ctx.ds
    out = {}
    for leaf_id in ctx.allowed_leaves:
        have = sum(ds.courses[c].credits for c in ctx.leaf_members(leaf_id) if c in ctx.state.satisfied)
        out[leaf_id] = max(0, ds.blocks[leaf_id].required_credits - have)
    return out


def recommend_next_term(ctx: PlanningContext, plan: Plan) -> NextTermAdvice:
    ds, cal = ctx.ds, ctx.calendar
    t0 = 0
    first = plan.terms[0] if plan.terms else None
    recommended_ids = {c.course_id for c in first.courses} if first else set()
    needs = _block_needs(ctx)
    from curriculum_planner.solver.plan_builder import course_badges

    def eligible(c: str) -> tuple[bool, str]:
        if not ctx.offered(c, t0):
            return False, "không mở"
        for d in ds.predecessors.get(c, []):
            if ctx.dep_satisfied(d):
                continue
            if d.type == DependencyType.CO_REQUISITE and d.source in recommended_ids:
                continue
            return False, f"chưa đủ điều kiện {d.source}"
        m = ds.courses[c].min_accumulated_credits
        if m and ctx.state.passed_credits < m:
            return False, f"cần tích lũy {m} TC"
        if ds.courses[c].final_term_only and plan.metrics.graduation_index != t0:
            return False, "chỉ học ở kỳ cuối"
        return True, ""

    def suggestion(c: str) -> CourseSuggestion:
        course = ds.courses[c]
        mandatory = c in ctx.mandatory
        unlocks = [d.target for d in ds.successors.get(c, []) if d.target in ctx.candidates]
        reasons = []
        if mandatory:
            reasons.append("Môn bắt buộc chưa hoàn thành.")
        useful = [lf for lf in ds.course_leaf_blocks.get(c, []) if needs.get(lf, 0) > 0]
        block = useful[0] if useful else (ds.course_leaf_blocks.get(c) or [None])[0]
        if not mandatory and useful:
            reasons.append(f"Tính vào khối «{ds.blocks[useful[0]].name}» (còn thiếu {needs[useful[0]]} TC).")
        if unlocks:
            reasons.append(f"Mở khóa {len(unlocks)} môn phía sau.")
        off = ds.offerings[c]
        if off.offers_per_year <= 1 or off.year_parity:
            kinds = "/".join(k.value for k in off.terms if k != TermKind.HE)
            reasons.append(f"Chỉ mở {kinds}{' hai năm một lần' if off.year_parity else ' mỗi năm một lần'}.")
        pref = ctx.pref.get(c, 0)
        if pref >= 6 and not mandatory:
            reasons.append("Phù hợp sở thích của bạn.")
        if c in ctx.state.failed:
            reasons.append("Bạn cần học lại môn này.")
        score = 3 * mandatory + ctx.risk.get(c, 1) / 5 + 0.5 * len(unlocks) + pref / 5
        return CourseSuggestion(
            course_id=c,
            name=course.name,
            credits=course.credits,
            mandatory=mandatory,
            block=block,
            score=round(score, 2),
            badges=course_badges(ctx, c),
            reasons=reasons,
        )

    recommended = [suggestion(c) for c in sorted(recommended_ids)]
    recommended.sort(key=lambda s: -s.score)
    alternatives = []
    for c in sorted(ctx.candidates - recommended_ids):
        ok, _ = eligible(c)
        if not ok or c in ctx.prefs.excluded:
            continue
        useful = c in ctx.mandatory or any(needs.get(lf, 0) > 0 for lf in ds.course_leaf_blocks.get(c, []))
        if useful:
            alternatives.append(suggestion(c))
    alternatives.sort(key=lambda s: (-s.score, s.course_id))

    warnings = []
    for s in recommended:
        off = ds.offerings[s.course_id]
        if off.offers_per_year <= 1 or off.year_parity:
            nxt = None
            for i in range(1, len(cal.terms)):
                if ctx.offered(s.course_id, i):
                    nxt = cal.label(i)
                    break
            wait = f"đợt mở kế tiếp là {nxt}" if nxt else "không còn đợt mở nào trước hạn"
            freq = "hai năm mới mở một lần" if off.year_parity else "mỗi năm chỉ mở một lần"
            warnings.append(f"{s.name} ({s.course_id}) {freq}: nếu không đăng ký kỳ này thì {wait}.")
    if first is None:
        return NextTermAdvice(
            term=cal.label(0),
            plan_id=plan.id,
            recommended=[],
            alternatives=alternatives,
            total_credits=0,
            min_credits=ctx.wmin,
            max_credits=ctx.cap(0),
            warnings=warnings,
        )
    return NextTermAdvice(
        term=first.label,
        plan_id=plan.id,
        recommended=recommended,
        alternatives=alternatives[:15],
        total_credits=first.credits,
        min_credits=first.min_credits,
        max_credits=first.max_credits,
        warnings=warnings,
    )
