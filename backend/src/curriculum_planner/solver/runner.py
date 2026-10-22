"""Giải tối ưu theo thứ tự ưu tiên (lexicographic) trên một mô hình CP-SAT đã dựng."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from curriculum_planner.solver.model_builder import BuiltModel

DEFAULT_TIME_LIMIT = float(os.environ.get("CPLAN_STAGE_TIME_LIMIT", "3.0"))
DEFAULT_WORKERS = int(os.environ.get("CPLAN_WORKERS", str(min(4, os.cpu_count() or 1))))


@dataclass
class Solution:
    status: str  # OPTIMAL | FEASIBLE
    assignment: dict[str, int]  # môn → chỉ số kỳ
    counted: dict[str, str]  # môn (đã đạt hoặc được xếp) → khối lá được tính
    stage_values: dict[str, int] = field(default_factory=dict)
    solve_ms: int = 0


class StageSolver:
    """Tối ưu lần lượt từng mục tiêu; sau mỗi stage cố định giá trị đạt được rồi mới sang stage sau."""

    def __init__(self, built: BuiltModel, time_limit: float | None = None, workers: int | None = None):
        self.b = built
        self.time_limit = time_limit or DEFAULT_TIME_LIMIT
        self.workers = workers or DEFAULT_WORKERS
        self.last: Solution | None = None
        self.last_objective: tuple[str, str] | None = None
        self.all_optimal = True
        self.elapsed_ms = 0

    def _solve(self) -> tuple[int, cp_model.CpSolver]:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.time_limit
        solver.parameters.num_workers = self.workers
        t0 = time.perf_counter()
        status = solver.solve(self.b.model)
        self.elapsed_ms += int((time.perf_counter() - t0) * 1000)
        return status, solver

    def _hint(self, sol: Solution) -> None:
        m = self.b.model
        m.clear_hints()
        for (c, t), v in self.b.x.items():
            m.add_hint(v, 1 if sol.assignment.get(c) == t else 0)

    def _extract(self, solver: cp_model.CpSolver, status: int) -> Solution:
        assignment = {c: t for (c, t), v in self.b.x.items() if solver.value(v)}
        counted = {c: leaf for (c, leaf), v in self.b.y.items() if solver.value(v)}
        return Solution(
            status="OPTIMAL" if status == cp_model.OPTIMAL and self.all_optimal else "FEASIBLE",
            assignment=assignment,
            counted=counted,
        )

    def run(self, stages: list[tuple[str, str]]) -> Solution | None:
        """`stages` = [(tên mục tiêu, 'min'|'max'), ...]. Trả None nếu vô nghiệm / hết giờ không có lời giải."""
        m = self.b.model
        if not stages:
            stages = [("grad", "min")]
        values: dict[str, int] = {}
        for name, sense in stages:
            expr = self.b.objectives.get(name)
            if expr is None or isinstance(expr, int):
                continue
            m.clear_objective()
            if sense == "min":
                m.minimize(expr)
            else:
                m.maximize(expr)
            if self.last is not None:
                self._hint(self.last)
            status, solver = self._solve()
            if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                if self.last is None:
                    return None
                break  # giữ lời giải stage trước
            if status != cp_model.OPTIMAL:
                self.all_optimal = False
            val = int(round(solver.objective_value))
            values[name] = val
            sol = self._extract(solver, status)
            sol.stage_values = dict(values)
            self.last = sol
            self.last_objective = (name, sense)
            if sense == "min":
                m.add(expr <= val)
            else:
                m.add(expr >= val)
        if self.last is not None:
            self.last.solve_ms = self.elapsed_ms
        return self.last

    def resolve_different_from(self, others: list[dict[str, int]]) -> Solution | None:
        """Tìm lời giải khác hẳn các phương án `others` mà vẫn giữ mọi giá trị tối ưu đã cố định."""
        m = self.b.model
        for other in others:
            terms = []
            for (c, t), v in self.b.x.items():
                terms.append((1 - v) if other.get(c) == t else v)
            m.add(sum(terms) >= 1)
        if self.last_objective is not None:
            name, sense = self.last_objective
            m.clear_objective()
            expr = self.b.objectives[name]
            m.minimize(expr) if sense == "min" else m.maximize(expr)
        m.clear_hints()
        status, solver = self._solve()
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None
        sol = self._extract(solver, status)
        sol.stage_values = dict(self.last.stage_values) if self.last else {}
        sol.solve_ms = self.elapsed_ms
        self.last = sol
        return sol
