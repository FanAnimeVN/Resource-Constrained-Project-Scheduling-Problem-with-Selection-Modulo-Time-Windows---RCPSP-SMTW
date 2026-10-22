"""Đọc một thư mục dataset (JSON) thành đối tượng `Dataset` cùng các chỉ mục tra cứu."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from pathlib import Path

from curriculum_planner.domain.models import (
    AdvisorConfig,
    Course,
    Curriculum,
    Dependency,
    DependencyType,
    Equivalence,
    KnowledgeBlock,
    Offering,
    Regulation,
    StudentProfile,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def data_root() -> Path:
    return Path(os.environ.get("CPLAN_DATA_DIR", REPO_ROOT / "data"))


@dataclass
class Dataset:
    id: str
    courses: dict[str, Course]
    dependencies: list[Dependency]
    offerings: dict[str, Offering]
    curriculum: Curriculum
    equivalences: list[Equivalence] = field(default_factory=list)
    advisor: AdvisorConfig | None = None
    regulations: dict[str, Regulation] = field(default_factory=dict)
    students: dict[str, StudentProfile] = field(default_factory=dict)
    path: Path | None = None

    # ---- chỉ mục khối kiến thức -------------------------------------------------

    @cached_property
    def blocks(self) -> dict[str, KnowledgeBlock]:
        return {b.id: b for b in self.curriculum.all_blocks()}

    @cached_property
    def parent(self) -> dict[str, str | None]:
        out: dict[str, str | None] = {}

        def visit(b: KnowledgeBlock, p: str | None) -> None:
            out[b.id] = p
            for c in b.children:
                visit(c, b.id)

        for b in self.curriculum.blocks:
            visit(b, None)
        return out

    @cached_property
    def depth(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for bid in self.blocks:
            d, p = 0, self.parent[bid]
            while p is not None:
                d, p = d + 1, self.parent[p]
            out[bid] = d
        return out

    def ancestors(self, block_id: str) -> list[str]:
        """Khối và mọi tổ tiên của nó (tính cả chính nó)."""
        out, cur = [], block_id
        while cur is not None:
            out.append(cur)
            cur = self.parent[cur]
        return out

    @cached_property
    def block_specialization(self) -> dict[str, str | None]:
        """Chuyên ngành mà khối thuộc về (kế thừa từ tổ tiên)."""
        out: dict[str, str | None] = {}
        for bid in self.blocks:
            spec = None
            for a in self.ancestors(bid):
                if self.blocks[a].specialization:
                    spec = self.blocks[a].specialization
                    break
            out[bid] = spec
        return out

    @cached_property
    def block_kind(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for bid in self.blocks:
            kind = "other"
            for a in self.ancestors(bid):
                if self.blocks[a].kind != "other":
                    kind = self.blocks[a].kind
                    break
            out[bid] = kind
        return out

    @cached_property
    def course_leaf_blocks(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for leaf in self.curriculum.leaf_blocks():
            for bc in leaf.courses:
                out.setdefault(bc.id, []).append(leaf.id)
        return out

    def mandatory_in(self, leaf_id: str) -> set[str]:
        return set(self.blocks[leaf_id].mandatory_ids())

    # ---- chỉ mục phụ thuộc ------------------------------------------------------

    @cached_property
    def predecessors(self) -> dict[str, list[Dependency]]:
        out: dict[str, list[Dependency]] = {}
        for d in self.dependencies:
            if d.type != DependencyType.MUTUALLY_EXCLUSIVE:
                out.setdefault(d.target, []).append(d)
        return out

    @cached_property
    def successors(self) -> dict[str, list[Dependency]]:
        out: dict[str, list[Dependency]] = {}
        for d in self.dependencies:
            if d.type != DependencyType.MUTUALLY_EXCLUSIVE:
                out.setdefault(d.source, []).append(d)
        return out

    @cached_property
    def exclusive_pairs(self) -> list[tuple[str, str]]:
        pairs = {
            tuple(sorted((d.source, d.target)))
            for d in self.dependencies
            if d.type == DependencyType.MUTUALLY_EXCLUSIVE
        }
        return sorted(pairs)

    @cached_property
    def equivalence_map(self) -> dict[str, str]:
        """Mã cũ/thay thế → mã gốc."""
        out: dict[str, str] = {}
        for e in self.equivalences:
            for eq in e.equivalents:
                out[eq] = e.canonical
        return out

    def specialization_name(self, spec_id: str | None) -> str | None:
        for s in self.curriculum.specializations:
            if s.id == spec_id:
                return s.name
        return None

    def regulation(self, reg_id: str | None = None) -> Regulation:
        if reg_id is None:
            reg_id = "default" if "default" in self.regulations else next(iter(self.regulations))
        if reg_id not in self.regulations:
            raise KeyError(f"Không có hồ sơ quy chế '{reg_id}' trong dataset '{self.id}'")
        return self.regulations[reg_id]


def _read(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_dataset_from_path(path: Path) -> Dataset:
    path = Path(path)
    courses = {c["id"]: Course.model_validate(c) for c in _read(path / "courses.json")}
    deps = [Dependency.model_validate(d) for d in _read(path / "dependencies.json")]
    offerings = {o["course"]: Offering.model_validate(o) for o in _read(path / "offerings.json")}
    curriculum = Curriculum.model_validate(_read(path / "curriculum.json"))
    equivalences = []
    if (path / "equivalences.json").exists():
        equivalences = [Equivalence.model_validate(e) for e in _read(path / "equivalences.json")]
    advisor = None
    if (path / "advisor.json").exists():
        advisor = AdvisorConfig.model_validate(_read(path / "advisor.json"))
    regulations: dict[str, Regulation] = {}
    reg_dir = path / "regulations"
    if reg_dir.is_dir():
        for f in sorted(reg_dir.glob("*.json")):
            regulations[f.stem] = Regulation.model_validate(_read(f))
    students: dict[str, StudentProfile] = {}
    stu_dir = path / "students"
    if stu_dir.is_dir():
        for f in sorted(stu_dir.glob("*.json")):
            s = StudentProfile.model_validate(_read(f))
            students[s.id] = s
    return Dataset(
        id=path.name,
        courses=courses,
        dependencies=deps,
        offerings=offerings,
        curriculum=curriculum,
        equivalences=equivalences,
        advisor=advisor,
        regulations=regulations,
        students=students,
        path=path,
    )


@lru_cache(maxsize=16)
def load_dataset(dataset_id: str) -> Dataset:
    path = data_root() / dataset_id
    if not path.is_dir():
        raise FileNotFoundError(f"Không tìm thấy dataset '{dataset_id}' tại {path}")
    return load_dataset_from_path(path)


def list_datasets() -> list[str]:
    root = data_root()
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / "curriculum.json").exists())
