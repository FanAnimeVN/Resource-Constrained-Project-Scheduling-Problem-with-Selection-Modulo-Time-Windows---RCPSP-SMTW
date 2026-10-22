"""Phân tích đồ thị phụ thuộc theo chu kỳ mở môn: ES/LS, chuỗi găng, điểm rủi ro.

"Modulo time windows": một môn chỉ được học ở những kỳ khớp quy tắc mở môn (HK1/HK2/Hè, năm chẵn/lẻ),
nên kỳ sớm nhất của môn sau = kỳ MỞ đầu tiên sau kỳ của môn trước, không đơn giản là +1.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from curriculum_planner.data.loader import Dataset
from curriculum_planner.domain.models import Dependency, DependencyType, Term, TermKind

DepSatisfied = Callable[[Dependency], bool]


def delta(dep: Dependency) -> int:
    return 0 if dep.type == DependencyType.CO_REQUISITE else 1


def offered_at(ds: Dataset, cid: str, term: Term) -> bool:
    off = ds.offerings.get(cid)
    return off is not None and off.is_offered(term)


def next_offered(ds: Dataset, cid: str, terms: list[Term], t: int) -> int | None:
    for i in range(max(t, 0), len(terms)):
        if offered_at(ds, cid, terms[i]):
            return i
    return None


def prev_offered(ds: Dataset, cid: str, terms: list[Term], t: int) -> int | None:
    for i in range(min(t, len(terms) - 1), -1, -1):
        if offered_at(ds, cid, terms[i]):
            return i
    return None


@dataclass
class Windows:
    es: dict[str, int | None]
    ls: dict[str, int | None]
    pred: dict[str, str | None]  # môn trước quyết định ES (để truy vết chuỗi găng)

    def chain(self, cid: str) -> list[str]:
        out = [cid]
        seen = {cid}
        cur = self.pred.get(cid)
        while cur is not None and cur not in seen:
            out.append(cur)
            seen.add(cur)
            cur = self.pred.get(cur)
        return list(reversed(out))


def earliest_starts(
    ds: Dataset,
    terms: list[Term],
    candidates: set[str],
    dep_satisfied: DepSatisfied,
    cum_capacity: list[int] | None = None,
    base_credits: int = 0,
) -> tuple[dict[str, int | None], dict[str, str | None]]:
    """ES_c = kỳ mở sớm nhất của c sau khi mọi môn trước (chưa thỏa) đã có thể học."""
    es: dict[str, int | None] = {}
    pred: dict[str, str | None] = {c: None for c in candidates}
    for c in candidates:
        lb = 0
        m = ds.courses[c].min_accumulated_credits
        if m and cum_capacity is not None:
            lb = len(terms)
            for t, cap in enumerate(cum_capacity):
                if base_credits + cap >= m:
                    lb = t
                    break
        es[c] = next_offered(ds, c, terms, lb)

    deps = [
        d for d in ds.dependencies if d.type != DependencyType.MUTUALLY_EXCLUSIVE and d.target in candidates
    ]
    for _ in range(len(candidates) + 2):
        changed = False
        for d in deps:
            b = d.target
            if dep_satisfied(d) or es[b] is None:
                continue
            a = d.source
            if a not in candidates or es.get(a) is None:
                es[b] = None
                pred[b] = a
                changed = True
                continue
            nb = next_offered(ds, b, terms, max(es[b], es[a] + delta(d)))
            if nb != es[b]:
                es[b] = nb
                pred[b] = a
                changed = True
        if not changed:
            break
    return es, pred


def latest_starts(
    ds: Dataset,
    terms: list[Term],
    candidates: set[str],
    required: set[str],
    dep_satisfied: DepSatisfied,
    deadline: int,
) -> dict[str, int | None]:
    """LS_c = kỳ mở muộn nhất của c để mọi môn kế tiếp BẮT BUỘC vẫn kịp trước hạn `deadline`.

    Chỉ lan truyền qua môn bắt buộc nên việc cắt tỉa theo LS không bao giờ loại mất lời giải hợp lệ.
    """
    ls: dict[str, int | None] = {c: prev_offered(ds, c, terms, deadline) for c in candidates}
    deps = [
        d
        for d in ds.dependencies
        if d.type != DependencyType.MUTUALLY_EXCLUSIVE
        and d.target in required
        and d.target in candidates
        and d.source in candidates
    ]
    for _ in range(len(candidates) + 2):
        changed = False
        for d in deps:
            if dep_satisfied(d):
                continue
            lb = ls.get(d.target)
            la = ls.get(d.source)
            if lb is None or la is None:
                continue
            na = prev_offered(ds, d.source, terms, min(la, lb - delta(d)))
            if na != la:
                ls[d.source] = na
                changed = True
        if not changed:
            break
    return ls


def descendants(ds: Dataset, cid: str, within: set[str]) -> set[str]:
    out: set[str] = set()
    stack = [cid]
    while stack:
        cur = stack.pop()
        for d in ds.successors.get(cur, []):
            if d.target in within and d.target not in out:
                out.add(d.target)
                stack.append(d.target)
    return out


def downstream_length(ds: Dataset, within: set[str]) -> dict[str, int]:
    """Số cạnh 'học trước' dài nhất phía sau mỗi môn (trong tập `within`)."""
    memo: dict[str, int] = {}
    visiting: set[str] = set()

    def visit(c: str) -> int:
        if c in memo:
            return memo[c]
        if c in visiting:  # chu trình song hành – bỏ qua
            return 0
        visiting.add(c)
        best = 0
        for d in ds.successors.get(c, []):
            if d.target in within:
                best = max(best, delta(d) + visit(d.target))
        visiting.discard(c)
        memo[c] = best
        return best

    for c in within:
        visit(c)
    return memo


def risk_scores(
    ds: Dataset, candidates: set[str], failed: Iterable[str]
) -> tuple[dict[str, int], dict[str, list[str]]]:
    """Điểm rủi ro 1..20 cho mỗi môn còn phải học, kèm danh sách yếu tố để giải trình."""
    failed = set(failed)
    down = downstream_length(ds, candidates)
    scores: dict[str, int] = {}
    factors: dict[str, list[str]] = {}
    for c in candidates:
        f: list[str] = []
        s = 1
        n_desc = len(descendants(ds, c, candidates))
        if n_desc:
            s += min(6, n_desc)
            f.append(f"mở khóa {n_desc} môn phía sau")
        if down.get(c, 0) >= 2:
            s += min(4, down[c])
            f.append(f"đầu chuỗi tiên quyết dài {down[c]} kỳ")
        off = ds.offerings.get(c)
        if off is not None:
            if off.year_parity:
                s += 4
                f.append("chỉ mở 2 năm một lần")
            elif off.offers_per_year <= 1:
                s += 3
                kinds = "/".join(k.value for k in off.terms if k != TermKind.HE)
                f.append(f"chỉ mở mỗi năm một lần ({kinds})")
        fr = ds.courses[c].historical_fail_rate
        if fr:
            s += round(fr * 10)
            f.append(f"tỉ lệ rớt lịch sử {round(fr * 100)}%")
        if c in failed:
            s += 3
            f.append("bạn đã từng rớt môn này")
        scores[c] = min(20, s)
        factors[c] = f
    return scores, factors


def curriculum_critical_path(ds: Dataset) -> tuple[int, list[str]]:
    """Số kỳ chính tối thiểu để một tân sinh viên học xong các môn bắt buộc (không học hè)."""
    terms = []
    t = Term(year=2000, kind=TermKind.HK1)
    for _ in range(40):
        terms.append(t)
        t = t.next(include_summer=False)
    candidates = set(ds.course_leaf_blocks) | {d.source for d in ds.dependencies}
    candidates = {c for c in candidates if c in ds.courses}
    reg = next(iter(ds.regulations.values()), None)
    cap = reg.max_credits_main if reg else 24
    cum = [cap * i for i in range(len(terms))]
    es, pred = earliest_starts(ds, terms, candidates, lambda d: False, cum, 0)
    windows = Windows(es=es, ls={}, pred=pred)

    def worst(ids: Iterable[str]) -> tuple[int, str | None]:
        best, arg = -1, None
        for c in ids:
            v = es.get(c)
            v = 10**6 if v is None else v
            if v > best:
                best, arg = v, c
        return best, arg

    global_mand: set[str] = set()
    spec_mand: dict[str, set[str]] = {}
    for leaf in ds.curriculum.leaf_blocks():
        spec = ds.block_specialization[leaf.id]
        if spec is None:
            global_mand.update(leaf.mandatory_ids())
        else:
            spec_mand.setdefault(spec, set()).update(leaf.mandatory_ids())
    g_val, g_arg = worst(global_mand)
    best_spec = None
    for ids in spec_mand.values():
        v = worst(ids)
        if best_spec is None or v[0] < best_spec[0]:
            best_spec = v
    if best_spec is not None and best_spec[0] > g_val:
        g_val, g_arg = best_spec
    if g_arg is None:
        return 0, []
    return g_val + 1, windows.chain(g_arg)
