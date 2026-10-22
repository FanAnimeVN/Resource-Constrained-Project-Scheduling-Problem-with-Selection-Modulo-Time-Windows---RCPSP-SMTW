"""Trích tập xung đột tối thiểu (MUS) theo nhóm luật nghiệp vụ + gợi ý nới lỏng.

Mỗi nhóm ràng buộc gắn một assumption literal. CP-SAT trả về một lõi (core) đủ để vô nghiệm;
sau đó lọc xóa (deletion filter): bỏ thử từng phần tử, nếu vẫn vô nghiệm thì bỏ hẳn.
Kết quả: tập luật mà bỏ BẤT KỲ luật nào cũng làm bài toán khả thi trở lại.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from ortools.sat.python import cp_model

from curriculum_planner.analysis.context import build_context
from curriculum_planner.data.loader import Dataset
from curriculum_planner.domain.models import (
    Conflict,
    InfeasibilityReport,
    Issue,
    Preferences,
    Regulation,
    StudentProfile,
    Suggestion,
)
from curriculum_planner.explain import messages_vi as msg
from curriculum_planner.solver.model_builder import BuiltModel, build_model


@dataclass
class MusResult:
    keys: list[tuple]
    minimal: bool
    feasible: bool = False


def _check(b: BuiltModel, keys: list[tuple], time_limit: float, minimize_grad: bool = False):
    m = b.model
    m.clear_assumptions()
    m.add_assumptions([b.groups[k][0] for k in keys])
    m.clear_objective()
    if minimize_grad:
        m.minimize(b.grad)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 1 if not minimize_grad else 4
    status = solver.solve(m)
    return status, solver


def find_mus(b: BuiltModel, budget_s: float = 20.0, check_s: float = 2.0) -> MusResult:
    keys = list(b.groups)
    t0 = time.perf_counter()
    status, solver = _check(b, keys, max(check_s, 5.0))
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return MusResult([], True, feasible=True)
    if status != cp_model.INFEASIBLE:
        return MusResult([], False)
    idx_to_key = {b.groups[k][0].Index(): k for k in keys}
    core = [idx_to_key[i] for i in solver.sufficient_assumptions_for_infeasibility() if i in idx_to_key]
    if not core:
        core = keys
    minimal = True
    current = list(core)
    for k in list(current):
        if k not in current:
            continue
        if time.perf_counter() - t0 > budget_s:
            minimal = False
            break
        trial = [x for x in current if x != k]
        st, sv = _check(b, trial, check_s)
        if st == cp_model.INFEASIBLE:
            new_core = {
                idx_to_key[j] for j in sv.sufficient_assumptions_for_infeasibility() if j in idx_to_key
            }
            current = [x for x in trial if not new_core or x in new_core]
        elif st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            minimal = False
    return MusResult(current, minimal)


def explain_infeasibility(
    ds: Dataset,
    profile: StudentProfile,
    regulation: Regulation,
    prefs: Preferences,
    spec: str | None,
    prechecks: list[Issue],
    budget_s: float = 20.0,
) -> InfeasibilityReport:
    ctx = build_context(ds, profile, prefs=prefs, spec=spec, mode="explain", regulation=regulation)
    b = build_model(ctx, "explain")
    res = find_mus(b, budget_s=budget_s)
    conflicts: list[Conflict] = []
    for k in res.keys:
        _, info = b.groups[k]
        conflicts.append(
            Conflict(
                code=info.code,
                message=info.message,
                courses=info.courses,
                terms=info.terms,
                relaxable=info.relaxable,
            )
        )
    conflicts.sort(key=lambda c: (c.code, c.message))

    suggestions: list[Suggestion] = []
    if not res.feasible:
        all_keys = list(b.groups)
        for k in res.keys:
            _, info = b.groups[k]
            if not info.relaxable:
                continue
            st, sv = _check(b, [x for x in all_keys if x != k], 5.0, minimize_grad=True)
            if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                grad = int(sv.value(b.grad))
                term = ctx.calendar.label(grad)
                kind = k[0]
                detail = info.terms[0] if info.terms else (info.courses[0] if info.courses else "")
                template = msg.RELAX.get(kind)
                if template:
                    suggestions.append(
                        Suggestion(
                            code=kind, message=template.format(term=term, detail=detail), graduation_term=term
                        )
                    )
        if not prefs.summer_enabled:
            p2 = prefs.model_copy(update={"summer_enabled": True})
            ctx2 = build_context(ds, profile, prefs=p2, spec=spec, mode="optimize", regulation=regulation)
            b2 = build_model(ctx2, "optimize")
            b2.model.minimize(b2.grad)
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = 5.0
            st = solver.solve(b2.model)
            if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                term = ctx2.calendar.label(int(solver.value(b2.grad)))
                suggestions.insert(
                    0,
                    Suggestion(
                        code="SUMMER", message=msg.RELAX["SUMMER"].format(term=term), graduation_term=term
                    ),
                )
    # gộp các gợi ý trùng nội dung
    seen, uniq = set(), []
    for s in suggestions:
        if s.message not in seen:
            seen.add(s.message)
            uniq.append(s)
    return InfeasibilityReport(
        summary=msg.INFEASIBLE_SUMMARY,
        prechecks=prechecks,
        conflicts=conflicts,
        minimal=res.minimal,
        suggestions=uniq,
    )
