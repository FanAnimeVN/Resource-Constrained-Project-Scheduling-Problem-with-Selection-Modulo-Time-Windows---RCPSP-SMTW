"""Chẩn đoán nhanh (điều kiện cần). Vi phạm bất kỳ điều kiện nào ⇒ chắc chắn vô nghiệm."""

from __future__ import annotations

from curriculum_planner.analysis.context import PlanningContext
from curriculum_planner.analysis.graph import earliest_starts
from curriculum_planner.domain.models import Issue
from curriculum_planner.explain import messages_vi as msg


def _block_deficit(ctx: PlanningContext) -> int:
    """Cận dưới số TC còn phải học: lấy max giữa thiếu hụt tổng và tổng thiếu hụt các khối cấp cao."""
    ds = ctx.ds
    allowed = set(ctx.allowed_leaves)
    total_def = 0
    for top in ds.curriculum.blocks:
        have = 0
        counted: set[str] = set()
        for leaf in top.leaves():
            if leaf.id not in allowed:
                continue
            for bc in leaf.courses:
                if bc.id in ctx.state.satisfied and bc.id not in counted:
                    counted.add(bc.id)
                    have += ds.courses[bc.id].credits
        total_def += max(0, top.required_credits - have)
    overall = max(0, ds.curriculum.total_credits_required - ctx.state.passed_credits)
    return max(total_def, overall)


def run_prechecks(ctx: PlanningContext) -> list[Issue]:
    ds, cal = ctx.ds, ctx.calendar
    issues: list[Issue] = []
    D = cal.deadline_index
    names = lambda ids: [f"{ds.courses[c].name} ({c})" for c in ids]  # noqa: E731

    if D < 0 or not cal.terms:
        issues.append(
            Issue(
                code="PC-00",
                message=msg.EXPIRED.format(deadline=cal.deadline_term.label),
                terms=[cal.deadline_term.label],
            )
        )
        return issues
    remaining_terms = sum(1 for i in range(min(D + 1, len(cal.terms))) if cal.is_main(i))

    # PC-03: môn bắt buộc không thể học
    for c in sorted(ctx.mandatory):
        if c not in ctx.candidates:
            reason = ctx.removed.get(c, "không đủ điều kiện")
            issues.append(
                Issue(
                    code="PC-03",
                    message=msg.MANDATORY_UNAVAILABLE.format(course=names([c])[0], reason=reason),
                    courses=[c],
                )
            )

    # PC-01: chuỗi tiên quyết dài hơn số kỳ còn lại (báo chuỗi dài nhất trước, không lặp môn)
    late = [c for c in ctx.mandatory & ctx.candidates if ctx.es.get(c) is None or ctx.es[c] > D]
    found = []
    for c in late:
        chain = _long_chain(ctx, c)
        found.append((_terms_needed(ctx, chain), chain, c))
    found.sort(key=lambda f: (-(f[0] if f[0] is not None else 10**6), f[2]))
    reported: set[str] = set()
    for need, chain, c in found:
        if set(chain) & reported:
            continue
        reported.update(chain)
        if need is None:
            issues.append(
                Issue(
                    code="PC-03",
                    message=msg.NO_OFFERING_LEFT.format(
                        course=names([c])[0], deadline=cal.deadline_term.label
                    ),
                    courses=[c],
                )
            )
            continue
        issues.append(
            Issue(
                code="PC-01",
                message=msg.CHAIN_TOO_LONG.format(
                    chain=" → ".join(names(chain)),
                    need=need,
                    have=remaining_terms,
                    deadline=cal.deadline_term.label,
                ),
                courses=chain,
                terms=[cal.deadline_term.label],
            )
        )

    # PC-02: sức chứa
    need_credits = _block_deficit(ctx)
    capacity = sum(ctx.cap(t) for t in range(min(D + 1, len(cal.terms))))
    if need_credits > capacity:
        issues.append(
            Issue(
                code="PC-02",
                message=msg.CAPACITY.format(need=need_credits, cap=capacity, terms=remaining_terms),
            )
        )

    # PC-04: khối không thể đủ TC
    for leaf_id in ctx.allowed_leaves:
        b = ds.blocks[leaf_id]
        possible = sum(ds.courses[c].credits for c in ctx.leaf_members(leaf_id) if ctx.available(c))
        if possible < b.required_credits:
            issues.append(
                Issue(
                    code="PC-04",
                    message=msg.BLOCK_IMPOSSIBLE.format(block=b.name, need=b.required_credits, have=possible),
                )
            )

    # PC-05: hai môn bắt buộc loại trừ nhau
    for a, b2 in ds.exclusive_pairs:
        need_a = a in ctx.mandatory or a in ctx.state.satisfied
        need_b = b2 in ctx.mandatory or b2 in ctx.state.satisfied
        if need_a and need_b and (a in ctx.mandatory or b2 in ctx.mandatory):
            issues.append(
                Issue(
                    code="PC-05",
                    message=msg.EXCLUSIVE_MANDATORY.format(a=names([a])[0], b=names([b2])[0]),
                    courses=[a, b2],
                )
            )
    return issues


def _long_chain(ctx: PlanningContext, course: str) -> list[str]:
    """Chuỗi tiên quyết quyết định ES của `course` khi KHÔNG giới hạn hạn chót."""
    terms = list(ctx.calendar.terms)
    # mở rộng horizon để tính được ES thật
    while len(terms) < len(ctx.calendar.terms) + 12:
        terms.append(terms[-1].next(include_summer=ctx.prefs.summer_enabled))
    es, pred = earliest_starts(ctx.ds, terms, ctx.candidates, ctx.dep_satisfied)
    chain = [course]
    cur = pred.get(course)
    while cur is not None and cur not in chain:
        chain.append(cur)
        cur = pred.get(cur)
    return list(reversed(chain))


def _terms_needed(ctx: PlanningContext, chain: list[str]) -> int | None:
    """Số kỳ (kể từ kỳ đầu tiên) cần để học hết chuỗi theo lịch mở môn."""
    terms = list(ctx.calendar.terms)
    while len(terms) < len(ctx.calendar.terms) + 12:
        terms.append(terms[-1].next(include_summer=ctx.prefs.summer_enabled))
    es, _ = earliest_starts(ctx.ds, terms, ctx.candidates, ctx.dep_satisfied)
    last = es.get(chain[-1])
    if last is None:
        return None
    return sum(1 for i in range(last + 1) if terms[i].is_main)
