"""Kiểm tra tính hợp lệ của dữ liệu CTĐT trước khi đưa vào solver (DV-01..DV-14)."""

from __future__ import annotations

from collections import Counter

from curriculum_planner.data.loader import Dataset
from curriculum_planner.domain.models import (
    STRICT_DEPENDENCIES,
    DependencyType,
    Issue,
    SelectionRule,
    Severity,
    ValidationReport,
)


def tarjan_scc(nodes: list[str], edges: dict[str, list[str]]) -> list[list[str]]:
    """Thuật toán Tarjan (lặp, không đệ quy) tìm các thành phần liên thông mạnh."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    result: list[list[str]] = []
    counter = 0

    for root in nodes:
        if root in index:
            continue
        work = [(root, iter(edges.get(root, [])))]
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, it = work[-1]
            advanced = False
            for nxt in it:
                if nxt not in index:
                    index[nxt] = low[nxt] = counter
                    counter += 1
                    stack.append(nxt)
                    on_stack.add(nxt)
                    work.append((nxt, iter(edges.get(nxt, []))))
                    advanced = True
                    break
                if nxt in on_stack:
                    low[node] = min(low[node], index[nxt])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == node:
                        break
                result.append(comp)
    return result


def find_dependency_cycles(ds: Dataset) -> list[list[str]]:
    """Chu trình gây bế tắc: SCC có chứa ít nhất một cạnh 'phải học trước' (tiên quyết/học trước).

    Song hành hai chiều (A ↔ B) là hợp lệ vì chỉ buộc học cùng kỳ.
    """
    edges: dict[str, list[str]] = {}
    nodes: set[str] = set()
    for d in ds.dependencies:
        if d.type == DependencyType.MUTUALLY_EXCLUSIVE:
            continue
        edges.setdefault(d.source, []).append(d.target)
        nodes.update((d.source, d.target))
    cycles = []
    for comp in tarjan_scc(sorted(nodes), edges):
        members = set(comp)
        strict_inside = any(
            d.type in STRICT_DEPENDENCIES and d.source in members and d.target in members
            for d in ds.dependencies
        )
        if strict_inside and (len(comp) > 1 or comp[0] in edges.get(comp[0], [])):
            cycles.append(sorted(comp))
    return cycles


def validate_dataset(ds: Dataset) -> ValidationReport:
    issues: list[Issue] = []

    def err(code: str, msg: str, courses=(), severity=Severity.ERROR):
        issues.append(Issue(code=code, severity=severity, message=msg, courses=list(courses)))

    courses = ds.courses
    # DV-01 trùng mã (đọc lại file thô vì dict đã khử trùng)
    if ds.path is not None:
        import json

        raw = json.loads((ds.path / "courses.json").read_text(encoding="utf-8"))
        for cid, n in Counter(c["id"] for c in raw).items():
            if n > 1:
                err("DV-01", f"Mã học phần {cid} bị khai báo {n} lần.", [cid])

    # DV-03 tín chỉ
    for c in courses.values():
        if c.credits <= 0:
            err("DV-03", f"Học phần {c.id} có số tín chỉ không hợp lệ ({c.credits}).", [c.id])

    # DV-02 tham chiếu
    for d in ds.dependencies:
        for cid in (d.source, d.target):
            if cid not in courses:
                err("DV-02", f"Quan hệ {d.type.value} tham chiếu tới mã không tồn tại: {cid}.", [cid])
    for cid in ds.offerings:
        if cid not in courses:
            err("DV-02", f"Lịch mở môn tham chiếu tới mã không tồn tại: {cid}.", [cid])
    for b in ds.blocks.values():
        for bc in b.courses:
            if bc.id not in courses:
                err("DV-02", f"Khối «{b.name}» chứa mã không tồn tại: {bc.id}.", [bc.id])
    for e in ds.equivalences:
        if e.canonical not in courses:
            err("DV-02", f"Bảng tương đương trỏ tới mã gốc không tồn tại: {e.canonical}.", [e.canonical])

    # DV-04 chu trình
    for cyc in find_dependency_cycles(ds):
        names = " → ".join(cyc + [cyc[0]])
        err("DV-04", f"Phát hiện chu trình phụ thuộc: {names}. Không thể xếp lịch cho các môn này.", cyc)

    # mandatory set (mọi khối không thuộc chuyên ngành)
    mandatory_global: set[str] = set()
    for leaf in ds.curriculum.leaf_blocks():
        if ds.block_specialization[leaf.id] is None:
            mandatory_global.update(leaf.mandatory_ids())

    # DV-05 lịch mở
    for cid, c in courses.items():
        if cid not in ds.offerings or not ds.offerings[cid].terms:
            sev = Severity.ERROR if cid in mandatory_global else Severity.WARNING
            err("DV-05", f"Học phần {cid} ({c.name}) chưa có lịch mở môn.", [cid], sev)

    # DV-06, DV-07 khối
    for b in ds.blocks.values():
        if b.children and b.courses:
            err("DV-07", f"Khối «{b.name}» vừa có khối con vừa chứa môn; chỉ khối lá được chứa môn.")
        if b.is_leaf:
            avail = sum(
                courses[bc.id].credits for bc in b.courses if bc.id in courses and courses[bc.id].is_active
            )
            if avail < b.required_credits:
                err(
                    "DV-06",
                    f"Khối «{b.name}» yêu cầu {b.required_credits} TC nhưng tổng TC các môn chỉ có {avail}.",
                )
            if b.rule == SelectionRule.PICK_K_OF_N and (b.k or 0) > len(b.courses):
                err("DV-06", f"Khối «{b.name}» yêu cầu chọn {b.k} môn nhưng chỉ có {len(b.courses)} môn.")
            mand = sum(courses[c].credits for c in b.mandatory_ids() if c in courses)
            if b.rule == SelectionRule.ALL_MANDATORY and mand < b.required_credits:
                err("DV-06", f"Khối bắt buộc «{b.name}» chỉ có {mand} TC < {b.required_credits} TC yêu cầu.")
        elif not b.specialization_group:
            child_sum = sum(c.required_credits for c in b.children)
            if child_sum < b.required_credits:
                err(
                    "DV-07",
                    f"Khối «{b.name}» yêu cầu {b.required_credits} TC nhưng tổng yêu cầu các khối con là {child_sum}.",
                    severity=Severity.WARNING,
                )

    # DV-08 tổng 138
    top = sum(b.required_credits for b in ds.curriculum.blocks)
    if top != ds.curriculum.total_credits_required:
        err(
            "DV-08",
            f"Tổng TC các khối cấp cao nhất ({top}) khác tổng TC tốt nghiệp ({ds.curriculum.total_credits_required}).",
            severity=Severity.WARNING,
        )

    # DV-09 hai môn bắt buộc loại trừ nhau
    for a, b in ds.exclusive_pairs:
        if a in mandatory_global and b in mandatory_global:
            err("DV-09", f"Hai môn bắt buộc {a} và {b} lại loại trừ nhau.", [a, b])

    # DV-10 chuyên ngành
    spec_ids = {s.id for s in ds.curriculum.specializations}
    for s in ds.curriculum.specializations:
        if s.block_id not in ds.blocks:
            err("DV-10", f"Chuyên ngành {s.id} trỏ tới khối không tồn tại: {s.block_id}.")
    for b in ds.blocks.values():
        if b.specialization and b.specialization not in spec_ids:
            err("DV-10", f"Khối «{b.name}» gắn chuyên ngành không tồn tại: {b.specialization}.")
        if b.specialization_group:
            for c in b.children:
                if not c.specialization:
                    err("DV-10", f"Khối con «{c.name}» của nhóm chuyên ngành chưa gắn mã chuyên ngành.")

    # DV-11 môn ngừng dạy nhưng bắt buộc
    for cid in mandatory_global:
        if cid in courses and not courses[cid].is_active:
            err("DV-11", f"Môn bắt buộc {cid} đã ngừng giảng dạy.", [cid])

    # DV-12 tương đương xung đột
    seen: dict[str, str] = {}
    for e in ds.equivalences:
        for eq in e.equivalents:
            if eq in seen and seen[eq] != e.canonical:
                err("DV-12", f"Mã {eq} được khai báo tương đương với cả {seen[eq]} và {e.canonical}.", [eq])
            seen[eq] = e.canonical

    # DV-13 phụ thuộc ra ngoài CTĐT
    in_curriculum = set(ds.course_leaf_blocks)
    for d in ds.dependencies:
        for cid in (d.source, d.target):
            if cid in courses and cid not in in_curriculum:
                err(
                    "DV-13",
                    f"Học phần {cid} có quan hệ phụ thuộc nhưng không thuộc khối nào của CTĐT.",
                    [cid],
                    Severity.WARNING,
                )

    # DV-14 chuỗi găng của CTĐT dài hơn số kỳ chuẩn (chỉ khi dữ liệu không có lỗi cấu trúc)
    if not any(i.severity == Severity.ERROR for i in issues):
        from curriculum_planner.analysis.graph import curriculum_critical_path

        length, chain = curriculum_critical_path(ds)
        if length > ds.curriculum.standard_main_terms:
            err(
                "DV-14",
                f"Chuỗi găng của CTĐT ({' → '.join(chain)}) cần {length} kỳ chính, dài hơn {ds.curriculum.standard_main_terms} kỳ chuẩn.",
                chain,
                Severity.WARNING,
            )

    return ValidationReport(dataset=ds.id, issues=issues)
