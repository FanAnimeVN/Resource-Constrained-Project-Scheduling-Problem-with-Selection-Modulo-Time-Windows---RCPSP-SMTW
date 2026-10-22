import pytest
from fastapi.testclient import TestClient

from curriculum_planner.api.app import app

client = TestClient(app)
DS = "hcmus_cntt_k2020"


def test_health_and_datasets():
    assert client.get("/api/health").json()["status"] == "ok"
    data = client.get("/api/datasets").json()
    ds = next(d for d in data if d["id"] == DS)
    assert ds["total_credits_required"] == 138
    assert {s["id"] for s in ds["students"]} == {"sv01", "sv02", "sv03", "sv04", "sv05"}
    assert {r["id"] for r in ds["regulations"]} >= {"default", "hcmus_clc_2025"}


def test_catalog_curriculum_validation_students():
    assert len(client.get(f"/api/datasets/{DS}/courses").json()["courses"]) == 91
    cur = client.get(f"/api/datasets/{DS}/curriculum").json()
    assert cur["curriculum"]["total_credits_required"] == 138
    assert client.get(f"/api/datasets/{DS}/validation").json()["issues"] == []
    assert client.get(f"/api/datasets/{DS}/students/sv03").json()["academic_warning"] is True
    assert client.get(f"/api/datasets/{DS}/students/nope").status_code == 404
    assert client.get("/api/datasets/khong-co/curriculum").status_code == 404


@pytest.mark.parametrize("sid,spec", [("sv01", "KHMT"), ("sv02", "CNPM"), ("sv03", None), ("sv05", "MMT")])
def test_plans_ok_for_sample_students(sid, spec):
    prefs = {"specialization": spec} if spec else None
    body = {"dataset": DS, "student_id": sid, "explain": False}
    if prefs:
        body["preferences"] = prefs
    r = client.post("/api/plans", json=body)
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "OK"
    assert len(res["plans"]) == 5
    assert res["comparison"]["rows"]


def test_infeasible_student_returns_report_not_error():
    r = client.post("/api/plans", json={"dataset": DS, "student_id": "sv04"})
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "INFEASIBLE"
    assert res["plans"] == []
    assert res["infeasibility"]["prechecks"][0]["code"] == "PC-01"
    assert res["infeasibility"]["conflicts"]


def test_regulation_profile_switch():
    r = client.post(
        "/api/plans",
        json={
            "dataset": DS,
            "student_id": "sv01",
            "regulation": "hcmus_clc_2025",
            "preferences": {"specialization": "KHMT"},
            "strategies": ["FAST_TRACK"],
            "explain": False,
        },
    ).json()
    assert all(t["credits"] <= 22 for t in r["plans"][0]["terms"])


def test_advisor_and_next_term_and_what_if():
    adv = client.post(
        "/api/advisor/specializations",
        json={"dataset": DS, "student_id": "sv02", "interests": {"networks": 5, "security": 5}},
    ).json()
    assert adv["ranking"][0]["specialization"] == "MMT"
    nt = client.post(
        "/api/recommendations/next-term",
        json={
            "dataset": DS,
            "student_id": "sv02",
            "preferences": {"specialization": "CNPM"},
            "strategy": "BALANCED",
        },
    ).json()
    assert nt["status"] == "OK"
    assert nt["advice"]["recommended"]
    assert nt["advice"]["min_credits"] <= nt["advice"]["total_credits"] <= nt["advice"]["max_credits"]
    plan = nt["plan_result"]["plans"][0]
    course = plan["terms"][0]["courses"][0]["course_id"]
    w = client.post(
        "/api/what-if/fail",
        json={
            "dataset": DS,
            "student_id": "sv02",
            "preferences": {"specialization": "CNPM"},
            "plan": plan,
            "course_id": course,
        },
    ).json()
    assert w["course_id"] == course and w["message"]
