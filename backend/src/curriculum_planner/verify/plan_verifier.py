"""Bộ kiểm chứng độc lập (oracle): kiểm tra một phương án theo đúng quy chế, KHÔNG dùng mô hình CP-SAT.

Mọi phương án đều phải qua đây trước khi trả về người dùng. Nó cũng là chuẩn đối chiếu cho
property-based test và cho phần giải trình phản thực tế ("nếu dời môn sang kỳ khác thì vi phạm luật nào").
"""

from __future__ import annotations

from dataclasses import dataclass, field

from curriculum_planner.analysis.context import PlanningContext
from curriculum_planner.domain.models import DependencyType, SelectionRule


@dataclass
class Violation:
    code: str
    message: str
    courses: list[str] = field(default_factory=list)
    terms: list[int] = field(default_factory=list)


def verify_plan(
    ctx: PlanningContext,
    assignment: dict[str, int],
    counted: dict[str, str],
    check_preferences: bool = True,
) -> list[Violation]:
    ds, cal, st = ctx.ds, ctx.calendar, ctx.state
    out: list[Violation] = []
    v = lambda code, m, cs=(), ts=(): out.append(Violation(code, m, list(cs), list(ts)))  # noqa: E731
    H = len(cal.terms)

    if not assignment:
        v("HC-01", "Phương án rỗng.")
        return out
    grad = max(assignment.values())

    # HC-02 không học lại môn đã đạt / môn không tồn tại
    for c, t in assignment.items():
        if c not in ds.courses:
            v("HC-02", f"Môn {c} không có trong danh mục.", [c])
            continue
        if c in st.satisfied:
            v("HC-02", f"Môn {c} đã đạt nhưng vẫn được xếp lại.", [c], [t])
        if not ds.courses[c].is_active:
            v("HC-02", f"Môn {c} đã ngừng giảng dạy.", [c], [t])
        if not 0 <= t < H:
            v("HC-11", f"Môn {c} xếp ngoài khoảng thời gian cho phép.", [c], [t])

    # HC-10 kỳ mở môn
    for c, t in assignment.items():
        if 0 <= t < H and not ctx.offered(c, t):
            v("HC-10", f"Môn {c} không mở ở {cal.label(t)}.", [c], [t])

    # HC-04/05/06 phụ thuộc
    for d in ds.dependencies:
        if d.type == DependencyType.MUTUALLY_EXCLUSIVE or d.target not in assignment:
            continue
        if ctx.dep_satisfied(d):
            continue
        tb = assignment[d.target]
        ta = assignment.get(d.source)
        code = {"PREREQUISITE": "HC-04", "PRE_COURSE": "HC-05", "CO_REQUISITE": "HC-06"}[d.type.value]
        ok = ta is not None and (ta <= tb if d.type == DependencyType.CO_REQUISITE else ta < tb)
        if not ok:
            v(code, f"{d.target} cần {d.source} ({d.type.value}).", [d.source, d.target], [tb])

    # HC-07 loại trừ
    taken = set(assignment) | set(st.satisfied)
    for a, b in ds.exclusive_pairs:
        if a in assignment and b in taken or b in assignment and a in taken:
            v("HC-07", f"{a} và {b} loại trừ nhau nhưng cùng có trong lộ trình.", [a, b])
        if a in counted and b in counted:
            v("HC-07", f"{a} và {b} loại trừ nhau nhưng cùng được tính tín chỉ.", [a, b])

    # HC-03 cấu trúc khối (qua chứng chỉ `counted`)
    allowed = set(ctx.allowed_leaves)
    for c, leaf in counted.items():
        if leaf not in allowed:
            v("HC-03", f"Môn {c} được tính vào khối {leaf} không thuộc chuyên ngành đã chọn.", [c])
        elif c not in ctx.leaf_members(leaf):
            v("HC-03", f"Môn {c} không thuộc khối {leaf}.", [c])
        if c not in assignment and c not in st.satisfied:
            v("HC-03", f"Môn {c} được tính tín chỉ nhưng chưa học.", [c])
    for c in assignment:
        if (
            c in ds.course_leaf_blocks
            and any(lf in allowed for lf in ds.course_leaf_blocks[c])
            and c not in counted
        ):
            v("HC-03", f"Môn {c} được xếp nhưng không được tính vào khối nào.", [c])
    for leaf_id in allowed:
        for m in ds.blocks[leaf_id].mandatory_ids():
            if counted.get(m) != leaf_id:
                v("HC-03", f"Thiếu môn bắt buộc {m} của khối {leaf_id}.", [m])
    for b in ds.blocks.values():
        spec = ds.block_specialization[b.id]
        if spec is not None and spec != ctx.spec:
            continue
        leaves = {lf.id for lf in b.leaves()}
        members = [c for c, lf in counted.items() if lf in leaves]
        credits = sum(ds.courses[c].credits for c in members)
        if credits < b.required_credits:
            v("HC-03", f"Khối «{b.name}» mới có {credits}/{b.required_credits} TC.")
        if b.rule == SelectionRule.PICK_K_OF_N and b.k and len(members) < b.k:
            v("HC-03", f"Khối «{b.name}» mới chọn {len(members)}/{b.k} môn.")

    # HC-01 tổng tín chỉ
    total = sum(ds.courses[c].credits for c in counted if ds.courses[c].counts_toward_total)
    req = ds.curriculum.total_credits_required
    if total < req or (ds.curriculum.credit_rule == "exact" and total != req):
        v(
            "HC-01",
            f"Tổng tín chỉ được tính là {total}, yêu cầu {'đúng' if ds.curriculum.credit_rule == 'exact' else 'tối thiểu'} {req}.",
        )

    # HC-08 / HC-09 tải
    loads = [0] * H
    for c, t in assignment.items():
        if 0 <= t < H:
            loads[t] += ds.courses[c].credits
    reg = ctx.regulation
    for t in range(H):
        if cal.is_main(t):
            if loads[t] > ctx.wmax:
                v("HC-08", f"{cal.label(t)} có {loads[t]} TC > trần {ctx.wmax}.", ts=[t])
            final = t == grad
            needs_floor = t <= grad and not (final and reg.final_term_min_exempt)
            if reg.allow_empty_main_terms and loads[t] == 0:
                needs_floor = False
            if needs_floor and loads[t] < ctx.wmin:
                v("HC-08", f"{cal.label(t)} có {loads[t]} TC < mức tối thiểu {ctx.wmin}.", ts=[t])
        elif loads[t] > ctx.wmax_summer:
            v("HC-09", f"{cal.label(t)} có {loads[t]} TC > trần hè {ctx.wmax_summer}.", ts=[t])

    # HC-11 hạn chót
    if grad > cal.deadline_index:
        v("HC-11", f"Tốt nghiệp ở {cal.label(grad)} vượt hạn {cal.deadline_term.label}.", ts=[grad])

    # điều kiện môn
    for c, t in assignment.items():
        course = ds.courses[c]
        if course.min_accumulated_credits:
            acc = st.passed_credits + sum(loads[:t])
            if acc < course.min_accumulated_credits:
                v("COURSE", f"{c} cần tích lũy {course.min_accumulated_credits} TC (mới có {acc}).", [c], [t])
        if course.final_term_only and t != grad:
            v("COURSE", f"{c} phải học ở học kỳ cuối.", [c], [t])
        if course.min_gpa is not None and st.gpa is not None and st.gpa < course.min_gpa:
            v("COURSE", f"{c} yêu cầu GPA ≥ {course.min_gpa}.", [c], [t])

    # tùy chọn của sinh viên
    if check_preferences:
        p = ctx.prefs
        if ctx.personal_max is not None:
            for t in range(H):
                if cal.is_main(t) and loads[t] > ctx.personal_max:
                    v("PREF", f"{cal.label(t)} vượt giới hạn cá nhân {ctx.personal_max} TC.", ts=[t])
        for pin in p.pinned:
            if pin.course in st.satisfied:
                continue
            if assignment.get(pin.course) != cal.index_of(pin.term):
                v("PREF", f"{pin.course} không được xếp vào {pin.term.label} như đã ghim.", [pin.course])
        for c in p.excluded:
            if c in assignment:
                v("PREF", f"{c} nằm trong danh sách không muốn học.", [c])
        if p.target_graduation_term is not None:
            if grad > cal.index_at_or_before(p.target_graduation_term):
                v("PREF", f"Tốt nghiệp muộn hơn kỳ mong muốn {p.target_graduation_term.label}.", ts=[grad])
    return out
