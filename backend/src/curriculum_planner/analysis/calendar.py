"""Sinh dãy học kỳ cần lập kế hoạch và hạn chót đào tạo."""

from __future__ import annotations

from dataclasses import dataclass

from curriculum_planner.domain.models import Term, TermKind


def main_term_number(cohort_year: int, term: Term) -> float:
    """Thứ tự kỳ chính (1-based) tính từ khóa. Kỳ hè trả về x.5 (nằm sau HK2 cùng năm)."""
    base = (term.year - cohort_year) * 2
    if term.kind == TermKind.HK1:
        return base + 1
    if term.kind == TermKind.HK2:
        return base + 2
    return base + 2.5


def nth_main_term(cohort_year: int, n: int) -> Term:
    year = cohort_year + (n - 1) // 2
    return Term(year=year, kind=TermKind.HK1 if n % 2 == 1 else TermKind.HK2)


@dataclass
class Calendar:
    terms: list[Term]
    deadline_index: int  # chỉ số kỳ cuối cùng còn trong hạn (−1 nếu đã hết hạn)
    deadline_term: Term
    standard_index: int  # chỉ số kỳ tốt nghiệp chuẩn (có thể < 0 nếu đã quá chuẩn)
    cohort_year: int

    def __len__(self) -> int:
        return len(self.terms)

    def label(self, i: int) -> str:
        if 0 <= i < len(self.terms):
            return self.terms[i].label
        return f"kỳ #{i + 1} (ngoài khoảng lập kế hoạch)"

    def is_main(self, i: int) -> bool:
        return 0 <= i < len(self.terms) and self.terms[i].is_main

    def index_of(self, term: Term) -> int | None:
        for i, t in enumerate(self.terms):
            if t == term:
                return i
        return None

    def main_indices(self) -> list[int]:
        return [i for i, t in enumerate(self.terms) if t.is_main]

    def index_at_or_before(self, term: Term) -> int:
        """Chỉ số kỳ muộn nhất trong lịch không vượt quá `term` (−1 nếu không có)."""
        best = -1
        for i, t in enumerate(self.terms):
            if t.sort_key <= term.sort_key:
                best = i
        return best


def build_calendar(
    cohort_year: int,
    next_term: Term,
    max_main_terms: int,
    standard_main_terms: int,
    summer_enabled: bool,
    extra_main_terms: int = 0,
) -> Calendar:
    """Dãy kỳ từ `next_term` tới hạn chót (+ `extra_main_terms` kỳ chính để chẩn đoán gia hạn).

    Hạn chót là kỳ chính thứ `max_main_terms` tính từ khóa; kỳ hè cùng năm học của kỳ đó vẫn trong hạn.
    """
    deadline_term = nth_main_term(cohort_year, max_main_terms)
    if summer_enabled and deadline_term.kind == TermKind.HK2:
        deadline_term = Term(year=deadline_term.year, kind=TermKind.HE)
    last_term = nth_main_term(cohort_year, max_main_terms + extra_main_terms)
    if summer_enabled and last_term.kind == TermKind.HK2:
        last_term = Term(year=last_term.year, kind=TermKind.HE)
    standard_term = nth_main_term(cohort_year, standard_main_terms)

    cur = next_term
    if cur.kind == TermKind.HE and not summer_enabled:
        cur = cur.next(include_summer=False)
    terms: list[Term] = []
    while cur.sort_key <= last_term.sort_key:
        terms.append(cur)
        cur = cur.next(include_summer=summer_enabled)

    cal = Calendar(
        terms=terms,
        deadline_index=-1,
        deadline_term=deadline_term,
        standard_index=-1,
        cohort_year=cohort_year,
    )
    cal.deadline_index = cal.index_at_or_before(deadline_term)
    cal.standard_index = cal.index_at_or_before(standard_term)
    return cal
