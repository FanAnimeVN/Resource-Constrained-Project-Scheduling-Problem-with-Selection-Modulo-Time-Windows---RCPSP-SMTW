from curriculum_planner.advisor.next_term import recommend_next_term
from curriculum_planner.advisor.specialization import _cosine, recommend_specializations
from curriculum_planner.advisor.what_if import simulate_fail
from curriculum_planner.analysis.context import build_context
from curriculum_planner.domain.models import Strategy
from curriculum_planner.solver.engine import plan_for_student


def test_cosine():
    assert _cosine({"a": 1}, {"a": 2}) == 1.0
    assert _cosine({"a": 1}, {"b": 1}) == 0.0
    assert _cosine({}, {"a": 1}) == 0.0


def test_advisor_ranks_by_interest_and_explains(ds):
    advice = recommend_specializations(ds, ds.students["sv02"])
    assert advice.top == "CNPM"
    top = advice.ranking[0]
    assert top.rank == 1 and 0 <= top.score <= 1
    assert any("sở thích" in r for r in top.reasons)
    assert all(r.feasible for r in advice.ranking)


def test_advisor_freshman_has_low_confidence(ds):
    advice = recommend_specializations(ds, ds.students["sv01"], run_progress=False)
    assert all(r.confidence == "thấp" for r in advice.ranking)
    assert advice.top in {"KHMT", "CNTT"}  # thích AI / dữ liệu


def test_advisor_weights_change_ranking(ds):
    s = ds.students["sv05"]
    only_interest = recommend_specializations(
        ds, s, weights={"interest": 1, "academic": 0, "career": 0, "progress": 0}, run_progress=False
    )
    assert only_interest.top == "MMT"


def test_next_term_recommendation_respects_offering(ds):
    s = ds.students["sv02"]
    prefs = s.preferences.model_copy(update={"specialization": "CNPM"})
    res = plan_for_student(ds, s, prefs=prefs, strategies=[Strategy.FAST_TRACK], explain=False)
    ctx = build_context(ds, s, prefs=prefs, spec="CNPM")
    adv = recommend_next_term(ctx, res.plans[0])
    assert adv.term == "HK2 2026–2027"
    for sug in adv.recommended + adv.alternatives:
        assert ctx.offered(sug.course_id, 0)
        assert sug.course_id not in ctx.state.satisfied


def test_what_if_fail_delays_or_keeps_graduation(ds):
    s = ds.students["sv01"]
    prefs = s.preferences.model_copy(update={"specialization": "KHMT"})
    res = plan_for_student(ds, s, prefs=prefs, strategies=[Strategy.FAST_TRACK], explain=False)
    plan = res.plans[0]
    w = simulate_fail(ds, s, plan, "CSC10004", prefs)
    assert w.status == "OK"
    assert w.delay_main_terms is not None and w.delay_main_terms >= 1
    assert "CSC10004" not in w.result.plans[0].passed_assignment
