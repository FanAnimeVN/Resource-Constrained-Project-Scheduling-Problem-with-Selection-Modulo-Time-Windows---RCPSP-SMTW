"""Chuyển các file CSV (xuất từ hệ thống của Phòng Đào tạo) thành dataset JSON chuẩn.

Định dạng chi tiết: docs/data-format.md.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def _bool(v: str, default: bool = False) -> bool:
    if v == "":
        return default
    return v.lower() in {"1", "true", "x", "yes", "co", "có"}


def _num(v: str, cast=int):
    return cast(v) if v != "" else None


def _list(v: str) -> list[str]:
    return [x.strip() for x in v.replace(",", ";").split(";") if x.strip()]


def import_csv_dir(src: Path, out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    courses, offerings = [], []
    for r in _rows(src / "courses.csv"):
        c = {
            "id": r["id"],
            "name": r["name"],
            "credits": int(r["credits"]),
            "workload": _num(r.get("workload", "")) or 3,
            "tags": _list(r.get("tags", "")),
            "is_active": _bool(r.get("is_active", ""), True),
            "final_term_only": _bool(r.get("final_term_only", "")),
            "source": r.get("source") or "csv",
        }
        for key, cast in (
            ("min_accumulated_credits", int),
            ("min_gpa", float),
            ("historical_fail_rate", float),
        ):
            val = _num(r.get(key, ""), cast)
            if val is not None:
                c[key] = val
        courses.append(c)
        terms = r.get("offering_terms", "")
        if terms:
            o = {"course": r["id"]}
            if terms.upper() in {
                "FALL_ONLY",
                "SPRING_ONLY",
                "EVERY_TERM",
                "SUMMER_ALLOWED",
                "ODD_YEARS_ONLY",
                "EVEN_YEARS_ONLY",
            }:
                o["pattern"] = terms.upper()
            else:
                o["terms"] = _list(terms.upper())
            if r.get("year_parity"):
                o["year_parity"] = r["year_parity"].lower()
            offerings.append(o)

    deps = [
        {
            "source": r["source"],
            "target": r["target"],
            "type": r["type"].upper(),
            **({"min_grade": float(r["min_grade"])} if r.get("min_grade") else {}),
        }
        for r in _rows(src / "dependencies.csv")
    ]

    members: dict[str, list[dict]] = {}
    for r in _rows(src / "memberships.csv"):
        members.setdefault(r["block_id"], []).append(
            {"id": r["course_id"], "mandatory": _bool(r.get("mandatory", ""))}
        )
    nodes: dict[str, dict] = {}
    parents: dict[str, str] = {}
    order: list[str] = []
    for r in _rows(src / "blocks.csv"):
        b = {
            "id": r["id"],
            "name": r["name"],
            "rule": (r.get("rule") or "MIN_CREDITS").upper(),
            "required_credits": int(r.get("required_credits") or 0),
            "kind": r.get("kind") or "other",
            "children": [],
            "courses": members.get(r["id"], []),
        }
        if r.get("k"):
            b["k"] = int(r["k"])
        if r.get("specialization"):
            b["specialization"] = r["specialization"]
        if _bool(r.get("specialization_group", "")):
            b["specialization_group"] = True
        nodes[r["id"]] = b
        order.append(r["id"])
        if r.get("parent"):
            parents[r["id"]] = r["parent"]
    roots = []
    for bid in order:
        if bid in parents:
            nodes[parents[bid]]["children"].append(nodes[bid])
        else:
            roots.append(nodes[bid])

    meta = (_rows(src / "curriculum.csv") or [{}])[0]
    curriculum = {
        "id": meta.get("id") or out.name,
        "name": meta.get("name") or out.name,
        "total_credits_required": int(meta.get("total_credits_required") or 138),
        "credit_rule": meta.get("credit_rule") or "at_least",
        "standard_main_terms": int(meta.get("standard_main_terms") or 8),
        "blocks": roots,
        "specializations": [
            {
                "id": r["id"],
                "name": r["name"],
                "block_id": r["block_id"],
                "description": r.get("description", ""),
            }
            for r in _rows(src / "specializations.csv")
        ],
        "graduation_conditions": _list(meta.get("graduation_conditions", "")),
    }

    eq: dict[tuple[str, str], list[str]] = {}
    for r in _rows(src / "equivalences.csv"):
        eq.setdefault((r["canonical"], (r.get("kind") or "EQUIVALENT").upper()), []).append(r["equivalent"])
    equivalences = [{"canonical": c, "equivalents": v, "kind": k} for (c, k), v in eq.items()]

    def dump(name: str, obj) -> None:
        p = out / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    dump("courses.json", courses)
    dump("offerings.json", offerings)
    dump("dependencies.json", deps)
    dump("curriculum.json", curriculum)
    dump("equivalences.json", equivalences)
    reg = (_rows(src / "regulation.csv") or [None])[0]
    if reg:
        dump(
            "regulations/default.json",
            {
                "id": "default",
                **{
                    k: (int(v) if v.isdigit() else _bool(v) if v.lower() in {"true", "false"} else v)
                    for k, v in reg.items()
                    if v != ""
                },
            },
        )
    return out
