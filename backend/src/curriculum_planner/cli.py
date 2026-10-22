"""Giao diện dòng lệnh `cplan`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from curriculum_planner.data.loader import load_dataset, load_dataset_from_path


def _ds(arg: str):
    p = Path(arg)
    return load_dataset_from_path(p) if p.is_dir() else load_dataset(arg)


def cmd_validate(args) -> int:
    from curriculum_planner.validation.validator import validate_dataset

    ds = _ds(args.dataset)
    report = validate_dataset(ds)
    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        print(
            f"Dataset {ds.id}: {len(ds.courses)} môn, {len(ds.dependencies)} quan hệ, {len(ds.blocks)} khối"
        )
        for i in report.issues:
            print(f"  [{i.severity.value}] {i.code}: {i.message}")
        print("Không có lỗi." if report.ok else f"{len(report.errors)} lỗi.")
    return 0 if report.ok else 1


def cmd_plan(args) -> int:
    from curriculum_planner.domain.models import Strategy, StudentProfile
    from curriculum_planner.solver.engine import plan_for_student

    ds = _ds(args.dataset)
    if args.student in ds.students:
        profile = ds.students[args.student]
    else:
        profile = StudentProfile.model_validate(json.loads(Path(args.student).read_text(encoding="utf-8")))
    prefs = profile.preferences
    if args.specialization:
        prefs = prefs.model_copy(update={"specialization": args.specialization})
    if args.summer:
        prefs = prefs.model_copy(update={"summer_enabled": True})
    strategies = [Strategy(s) for s in args.strategy] if args.strategy else None
    res = plan_for_student(ds, profile, args.regulation, prefs, strategies, explain=not args.no_explain)
    if args.json:
        print(res.model_dump_json(indent=2))
        return 0
    print(f"Sinh viên {profile.name} – trạng thái: {res.status}")
    if res.specialization:
        print(f"Chuyên ngành: {res.specialization_name} ({res.specialization_source})")
    for w in res.warnings:
        print(f"  ! {w}")
    for p in res.plans:
        m = p.metrics
        print(
            f"\n== {p.title} – tốt nghiệp {m.graduation_term}, std tải {m.load_std}, đệm rủi ro {m.risk_coverage:.0%}"
        )
        for t in p.terms:
            names = ", ".join(c.course_id for c in t.courses)
            print(f"  {t.label:16} {t.credits:3d} TC | {names}")
    if res.infeasibility:
        print("\n" + res.infeasibility.summary)
        for i in res.infeasibility.prechecks:
            print(f"  [{i.code}] {i.message}")
        for c in res.infeasibility.conflicts:
            print(f"  - {c.message}")
        for s in res.infeasibility.suggestions:
            print(f"  > {s.message}")
    return 0


def cmd_advise(args) -> int:
    from curriculum_planner.advisor.specialization import recommend_specializations

    ds = _ds(args.dataset)
    advice = recommend_specializations(ds, ds.students[args.student], args.regulation)
    if args.json:
        print(advice.model_dump_json(indent=2))
        return 0
    for r in advice.ranking:
        c = r.components
        print(
            f"{r.rank}. {r.name}: {r.score:.3f} (A={c.academic:.2f} I={c.interest:.2f} C={c.career:.2f} P={c.progress:.2f})"
        )
        for reason in r.reasons:
            print(f"     - {reason}")
    print(advice.stability_note)
    return 0


def cmd_import_csv(args) -> int:
    from curriculum_planner.data.csv_import import import_csv_dir

    out = import_csv_dir(Path(args.src), Path(args.out))
    print(f"Đã ghi dataset vào {out}")
    return cmd_validate(argparse.Namespace(dataset=str(out), json=False))


def cmd_export_openapi(args) -> int:
    from curriculum_planner.api.app import app

    text = json.dumps(app.openapi(), ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cplan", description="Lập lộ trình học tập cá nhân hóa (RCPSP-SMTW)")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Kiểm tra dữ liệu CTĐT")
    v.add_argument("dataset")
    v.add_argument("--json", action="store_true")
    v.set_defaults(fn=cmd_validate)

    pl = sub.add_parser("plan", help="Lập lộ trình cho một sinh viên")
    pl.add_argument("--dataset", default="hcmus_cntt_k2020")
    pl.add_argument("--student", required=True, help="Mã SV mẫu (sv01…) hoặc đường dẫn file JSON hồ sơ")
    pl.add_argument("--regulation", default=None)
    pl.add_argument("--specialization", default=None)
    pl.add_argument("--strategy", action="append", help="FAST_TRACK | BALANCED | RISK_AVERSE | …")
    pl.add_argument("--summer", action="store_true", help="Bật học kỳ hè")
    pl.add_argument("--no-explain", action="store_true")
    pl.add_argument("--json", action="store_true")
    pl.set_defaults(fn=cmd_plan)

    a = sub.add_parser("advise", help="Tư vấn chọn chuyên ngành")
    a.add_argument("--dataset", default="hcmus_cntt_k2020")
    a.add_argument("--student", required=True)
    a.add_argument("--regulation", default=None)
    a.add_argument("--json", action="store_true")
    a.set_defaults(fn=cmd_advise)

    im = sub.add_parser("import-csv", help="Chuyển thư mục CSV của Phòng Đào tạo thành dataset JSON")
    im.add_argument("src")
    im.add_argument("out")
    im.set_defaults(fn=cmd_import_csv)

    ex = sub.add_parser("export-openapi", help="Xuất đặc tả OpenAPI")
    ex.add_argument("--out", default=None)
    ex.set_defaults(fn=cmd_export_openapi)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
