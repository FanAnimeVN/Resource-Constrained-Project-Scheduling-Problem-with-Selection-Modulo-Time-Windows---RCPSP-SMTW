import json

from helpers import block, mini_dataset, student

from curriculum_planner.analysis.context import build_context
from curriculum_planner.analysis.prechecks import run_prechecks
from curriculum_planner.data.csv_import import import_csv_dir
from curriculum_planner.data.loader import load_dataset_from_path
from curriculum_planner.domain.models import Strategy
from curriculum_planner.solver.engine import plan_for_student
from curriculum_planner.validation.validator import validate_dataset


def test_capacity_precheck():
    d = mini_dataset(
        [(f"C{i}", 4) for i in range(8)],
        [block("K", [f"C{i}" for i in range(8)], 32, rule="ALL_MANDATORY")],
        total=32,
        regulation={"min_credits_main": 0, "max_credits_main": 8, "max_main_terms": 8},
    )
    ctx = build_context(d, student(cohort=2023))  # còn 2 kỳ × 8 TC = 16 < 32
    codes = {i.code for i in run_prechecks(ctx)}
    assert "PC-02" in codes


def test_unavailable_mandatory_precheck():
    d = mini_dataset(
        [("A", 3), ("B", 3)],
        [block("K", ["A", "B"], 6, rule="ALL_MANDATORY")],
        total=6,
        course_extra={"B": {"is_active": False}},
    )
    ctx = build_context(d, student())
    assert any(i.code == "PC-03" for i in run_prechecks(ctx))


def test_completed_student():
    from curriculum_planner.domain.models import AcademicRecord

    d = mini_dataset([("A", 3)], [block("K", ["A"], 3, rule="ALL_MANDATORY")], total=3)
    res = plan_for_student(
        d, student(records=[AcademicRecord(course="A", status="PASSED")]), strategies=[Strategy.FAST_TRACK]
    )
    assert res.status == "COMPLETED"


def test_csv_import_roundtrip(tmp_path):
    src = tmp_path / "csv"
    src.mkdir()
    (src / "courses.csv").write_text(
        "id,name,credits,workload,tags,offering_terms\n"
        "A,Môn A,3,3,programming,HK1;HK2\n"
        "B,Môn B,3,3,programming,FALL_ONLY\n"
        "C,Môn C,4,2,,EVERY_TERM\n",
        encoding="utf-8",
    )
    (src / "dependencies.csv").write_text("source,target,type\nA,B,prerequisite\n", encoding="utf-8")
    (src / "blocks.csv").write_text(
        "id,name,parent,rule,required_credits\nROOT,Toàn khóa,,MIN_CREDITS,10\nBB,Bắt buộc,ROOT,ALL_MANDATORY,6\nTC,Tự chọn,ROOT,MIN_CREDITS,4\n",
        encoding="utf-8",
    )
    (src / "memberships.csv").write_text(
        "block_id,course_id,mandatory\nBB,A,1\nBB,B,1\nTC,C,0\n", encoding="utf-8"
    )
    (src / "curriculum.csv").write_text("id,name,total_credits_required\nDEMO,Demo,10\n", encoding="utf-8")
    (src / "regulation.csv").write_text(
        "name,min_credits_main,max_credits_main,max_main_terms\nDemo,3,10,8\n", encoding="utf-8"
    )
    out = import_csv_dir(src, tmp_path / "demo")
    d = load_dataset_from_path(out)
    assert validate_dataset(d).ok
    assert d.offerings["B"].terms == ["HK1"]
    assert json.loads((out / "regulations" / "default.json").read_text())["max_credits_main"] == 10
    res = plan_for_student(d, student(), strategies=[Strategy.FAST_TRACK], explain=False)
    assert res.status == "OK"
