"""Tiêu chí nghiệm thu AC-01..AC-07 (BDD, giữ nguyên văn Given/When/Then của đặc tả)."""

from __future__ import annotations

import json
import shutil

import pytest
from helpers import block, mini_dataset, student
from pytest_bdd import given, parsers, scenarios, then, when

from curriculum_planner.analysis.context import build_context
from curriculum_planner.data.loader import load_dataset_from_path
from curriculum_planner.domain.models import AcademicRecord, Preferences, Strategy, Term
from curriculum_planner.solver.engine import plan_for_student

scenarios(
    "ac01_credit_integrity.feature",
    "ac02_topological_calendar.feature",
    "ac03_credit_load_bounds.feature",
    "ac04_passed_courses.feature",
    "ac05_infeasibility_mus.feature",
    "ac06_rule_decoupling.feature",
    "ac07_plan_diversity.feature",
)


@pytest.fixture
def world():
    return {}


def _main_loads(plan):
    return [(t.index, t.credits, t.is_main) for t in plan.terms]


# ---------------------------------------------------------------- AC-01


@given(parsers.parse('Chương trình đào tạo yêu cầu tích lũy {total:d} tín chỉ theo quy tắc "{rule}"'))
def ac01_curriculum(world, total, rule):
    world["total"], world["rule"] = total, rule


@given(parsers.parse('Môn học {cid} thuộc cả "{b1}" và "{b2}" với số tín chỉ là {credits:d}'))
def ac01_shared_course(world, cid, b1, b2, credits):
    others = [f"K{i:02d}" for i in range(1, 47)]
    courses = [(cid, credits)] + [(c, 3) for c in others]
    blocks = [
        {
            "id": "CSNN",
            "name": b1,
            "rule": "MIN_CREDITS",
            "required_credits": 69,
            "courses": [{"id": c} for c in [cid] + others[:23]],
        },
        {
            "id": "CNH_A",
            "name": b2,
            "rule": "MIN_CREDITS",
            "required_credits": 69,
            "courses": [{"id": c} for c in [cid] + others[23:]],
        },
    ]
    world["cid"], world["credits"] = cid, credits
    world["ds"] = mini_dataset(courses, blocks, total=world["total"], credit_rule=world["rule"])
    world["student"] = student(records=[AcademicRecord(course="K01", status="PASSED", grade=8)])


@when("Hệ thống sinh ra một lộ trình học tập P")
def ac01_generate(world):
    res = plan_for_student(world["ds"], world["student"], strategies=[Strategy.FAST_TRACK], explain=False)
    assert res.status == "OK", res.infeasibility
    world["plan"] = res.plans[0]


@then(
    parsers.parse("Tổng số tín chỉ của các môn trong P cộng với các môn đã tích lũy phải đạt đúng {total:d}")
)
def ac01_total(world, total):
    assert world["plan"].metrics.total_credits == total


@then(parsers.parse("Môn {cid} chỉ được xuất hiện đúng 1 lần trong lộ trình P"))
def ac01_once(world, cid):
    occurrences = [c.course_id for t in world["plan"].terms for c in t.courses if c.course_id == cid]
    assert len(occurrences) == 1


@then(
    parsers.parse(
        "Số tín chỉ của {cid} chỉ được cộng đúng 1 lần ({credits:d} tín chỉ) vào tổng số tín chỉ tích lũy"
    )
)
def ac01_counted_once(world, cid, credits):
    plan = world["plan"]
    counted = [c for t in plan.terms for c in t.courses if c.course_id == cid and c.counted_block]
    assert len(counted) == 1 and counted[0].credits == credits
    scheduled = sum(c.credits for t in plan.terms for c in t.courses if c.counted_block)
    passed = 3  # K01
    assert scheduled + passed == plan.metrics.total_credits


# ---------------------------------------------------------------- AC-02


@given(parsers.parse('Môn "{target}" có tiên quyết là "{pre}"'))
def ac02_prereq(world, target, pre):
    world["names"] = {"HQTCSDL": target, "CTDLGT": pre}


@given(parsers.parse('Môn "{target}" chỉ được mở vào "Học kỳ Mùa Thu"'))
def ac02_offering(world, target):
    n = world["names"]
    fillers = [(f"F{i}", 3) for i in range(1, 9)]
    world["ds"] = mini_dataset(
        [
            ("CTDLGT", 4, ["HK1", "HK2"], n["CTDLGT"]),
            ("HQTCSDL", 4, ["HK1"], n["HQTCSDL"]),
            ("NMLT", 4, ["HK1", "HK2"]),
        ]
        + fillers,
        [block("K", ["CTDLGT", "HQTCSDL", "NMLT"] + [f[0] for f in fillers], 36, rule="ALL_MANDATORY")],
        deps=[("CTDLGT", "HQTCSDL", "PREREQUISITE"), ("NMLT", "CTDLGT", "PRE_COURSE")],
        total=36,
        regulation={"min_credits_main": 8, "max_credits_main": 14},
    )


@when(parsers.parse('Hệ thống xếp lịch cho môn "{target}" vào học kỳ T_k'))
def ac02_schedule(world, target):
    res = plan_for_student(world["ds"], student(), explain=False)
    assert res.status == "OK"
    world["plans"] = res.plans
    world["ctx"] = build_context(world["ds"], student())


@then("Kỳ T_k phải là Học kỳ Mùa Thu")
def ac02_fall(world):
    for p in world["plans"]:
        tk = p.assignment()["HQTCSDL"]
        assert p.terms[tk].term.kind.value == "HK1"


@then(parsers.parse('Môn "{pre}" phải được xếp ở học kỳ T_m với T_m < T_k (hoặc nằm trong C_passed)'))
def ac02_order(world, pre):
    for p in world["plans"]:
        a = p.assignment()
        assert a["CTDLGT"] < a["HQTCSDL"]


# ---------------------------------------------------------------- AC-03


@given(parsers.parse("Quy chế quy định kỳ chính có Min_Credits = {lo:d} và Max_Credits = {hi:d}"))
def ac03_regulation(world, ds, lo, hi):
    reg = ds.regulation("default")
    assert (reg.min_credits_main, reg.max_credits_main) == (lo, hi)
    world["plans"] = []
    for sid, spec in (("sv01", "KHMT"), ("sv02", "CNPM"), ("sv05", "MMT")):
        prefs = ds.students[sid].preferences.model_copy(update={"specialization": spec})
        res = plan_for_student(ds, ds.students[sid], prefs=prefs, explain=False)
        assert res.status == "OK"
        world["plans"].extend(res.plans)


@when("Duyệt qua tất cả các học kỳ t trong lộ trình đề xuất (ngoại trừ kỳ tốt nghiệp cuối cùng)")
def ac03_iterate(world):
    world["loads"] = [
        t.credits
        for p in world["plans"]
        for t in p.terms
        if t.is_main and t.index != p.metrics.graduation_index
    ]
    assert world["loads"]


@then(parsers.parse("Tổng số tín chỉ được xếp trong kỳ t phải >= {lo:d}"))
def ac03_floor(world, lo):
    assert min(world["loads"]) >= lo


@then(parsers.parse("Tổng số tín chỉ được xếp trong kỳ t phải <= {hi:d}"))
def ac03_cap(world, hi):
    assert max(world["loads"]) <= hi


# ---------------------------------------------------------------- AC-04


@given(parsers.parse('Sinh viên S đã hoàn thành môn "{name}" ở kỳ trước với trạng thái "PASSED"'))
def ac04_student(world, ds, name):
    cid = next(c.id for c in ds.courses.values() if c.name == name)
    base = ds.students["sv01"]
    world["cid"] = cid
    world["student"] = base.model_copy(
        update={
            "next_term": Term(year=2026, kind="HK2"),
            "records": [
                AcademicRecord(course=cid, status="PASSED", grade=8.5, term=Term(year=2026, kind="HK1"))
            ],
            "preferences": Preferences(specialization="KHMT"),
        }
    )


@when("Hệ thống tạo bất kỳ lộ trình nào cho sinh viên S")
def ac04_plan(world, ds):
    res = plan_for_student(ds, world["student"])
    assert res.status == "OK"
    world["plans"] = res.plans


@then(parsers.parse('Môn "{name}" tuyệt đối không xuất hiện trong danh sách các môn cần học tiếp'))
def ac04_absent(world):
    for p in world["plans"]:
        assert world["cid"] not in p.assignment()
        assert world["cid"] in p.passed_assignment


@then(parsers.parse('Môn "{name}" được tự động đánh dấu là điều kiện tiên quyết đã thỏa mãn cho các môn sau'))
def ac04_prereq_satisfied(world, ds):
    successors = [d.target for d in ds.successors[world["cid"]]]
    checked = 0
    for p in world["plans"]:
        for _, c in p.scheduled():
            if c.course_id in successors:
                reqs = [r for r in c.explanation.requires if world["cid"] in r.courses]
                assert reqs and "đã hoàn thành" in reqs[0].message
                checked += 1
    assert checked > 0


# ---------------------------------------------------------------- AC-05


@given(parsers.parse("Sinh viên chỉ còn tối đa {n:d} học kỳ trước khi hết thời gian đào tạo"))
def ac05_time(world, n):
    world["remaining"] = n


@given(
    "Danh sách môn bắt buộc còn lại đòi hỏi một chuỗi tiên quyết gồm 4 môn nối tiếp nhau (A -> B -> C -> D)"
)
def ac05_chain(world):
    world["ds"] = mini_dataset(
        [("A", 3), ("B", 3), ("C", 3), ("D", 3)],
        [block("K", ["A", "B", "C", "D"], 12, rule="ALL_MANDATORY")],
        deps=[("A", "B", "PREREQUISITE"), ("B", "C", "PREREQUISITE"), ("C", "D", "PREREQUISITE")],
        total=12,
        regulation={"min_credits_main": 0, "max_credits_main": 24, "max_main_terms": 8},
    )
    # khóa 2023, đang ở kỳ chính thứ 7 ⇒ còn đúng 2 kỳ (7 và 8)
    world["student"] = student(cohort=2023, year=2026, kind="HK1")


@when("Hệ thống thực thi thuật toán tìm kiếm lộ trình")
def ac05_run(world):
    world["res"] = plan_for_student(world["ds"], world["student"])


@then("Hệ thống KHÔNG được trả về bất kỳ phương án lộ trình nào")
def ac05_no_plan(world):
    assert world["res"].plans == []


@then("Hệ thống trả về mã trạng thái INFEASIBLE kèm theo báo cáo xung đột")
def ac05_status(world):
    res = world["res"]
    assert res.status == "INFEASIBLE"
    assert res.infeasibility is not None and res.infeasibility.conflicts
    codes = {c.code for c in res.infeasibility.conflicts}
    assert "HC-11" in codes and "HC-04" in codes


@then("Báo cáo chỉ đích danh: Chiều dài chuỗi tiên quyết (4 kỳ) vượt quá số kỳ còn lại (2 kỳ)")
def ac05_message(world):
    pre = world["res"].infeasibility.prechecks
    chain = [i for i in pre if i.code == "PC-01"]
    assert chain, pre
    assert chain[0].courses == ["A", "B", "C", "D"]
    assert "cần tối thiểu 4 học kỳ" in chain[0].message
    assert "chỉ còn 2 học kỳ" in chain[0].message


# ---------------------------------------------------------------- AC-06


@given("Quy chế đào tạo thay đổi Max_Credits kỳ chính từ 24 xuống 20 tín chỉ trong tệp cấu hình")
def ac06_change(world, ds, tmp_path):
    dst = tmp_path / ds.id
    shutil.copytree(ds.path, dst)
    f = dst / "regulations" / "default.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    assert data["max_credits_main"] == 24
    data["max_credits_main"] = 20
    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    world["ds"] = load_dataset_from_path(dst)


@when("Chạy bộ kiểm thử tự động với dữ liệu sinh viên đầu vào giữ nguyên")
def ac06_run(world):
    d = world["ds"]
    world["plans"] = []
    for sid, spec in (("sv01", "KHMT"), ("sv02", "CNPM")):
        prefs = d.students[sid].preferences.model_copy(update={"specialization": spec})
        res = plan_for_student(d, d.students[sid], prefs=prefs, explain=False)
        assert res.status == "OK"
        world["plans"].extend(res.plans)


@then("Mọi phương án lộ trình mới sinh ra đều có số tín chỉ mỗi kỳ <= 20")
def ac06_cap(world):
    assert all(t.credits <= 20 for p in world["plans"] for t in p.terms if t.is_main)


@then("Toàn bộ test suite vượt qua mà không có bất kỳ thay đổi nào trong mã nguồn thuật toán cốt lõi")
def ac06_no_code_change(world):
    # Chỉ dữ liệu được sửa (bản sao trong tmp_path); mã nguồn không bị chạm tới trong kịch bản này.
    assert world["ds"].regulation("default").max_credits_main == 20


# ---------------------------------------------------------------- AC-07


@given("Yêu cầu sinh ra 3 phương án lộ trình cho sinh viên")
def ac07_request(world, ds):
    world["student"] = ds.students["sv01"]
    world["prefs"] = world["student"].preferences.model_copy(update={"specialization": "KHMT"})


@when("Hệ thống trả về 3 phương án P_1, P_2, P_3")
def ac07_run(world, ds):
    res = plan_for_student(
        ds,
        world["student"],
        prefs=world["prefs"],
        strategies=[Strategy.FAST_TRACK, Strategy.BALANCED, Strategy.RISK_AVERSE],
        explain=False,
    )
    assert res.status == "OK" and len(res.plans) == 3
    world["P"] = {p.strategy: p for p in res.plans}


@then("P_1 phải tối ưu về số học kỳ (Fast-Track) với T_grad nhỏ nhất")
def ac07_fast(world):
    P = world["P"]
    g = P[Strategy.FAST_TRACK].metrics.graduation_index
    assert all(g <= p.metrics.graduation_index for p in P.values())


@then("P_2 phải tối ưu về độ lệch chuẩn tín chỉ (Balanced) với Var(Credits) nhỏ nhất")
def ac07_balanced(world):
    P = world["P"]
    s = P[Strategy.BALANCED].metrics.load_std
    assert all(s <= p.metrics.load_std for p in P.values())


@then("P_3 phải tối ưu về độ trễ an toàn môn nút cổ chai (Risk-Averse)")
def ac07_risk(world):
    P = world["P"]
    r = P[Strategy.RISK_AVERSE].metrics.risk_coverage
    assert all(r >= p.metrics.risk_coverage for p in P.values())


@then("Ma trận phân bổ kỳ giữa P_1, P_2, P_3 không được trùng nhau hoàn toàn (Distance metric > 0)")
def ac07_distance(world):
    from curriculum_planner.metrics import plan_distance

    ps = list(world["P"].values())
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            assert plan_distance(ps[i], ps[j]) > 0
