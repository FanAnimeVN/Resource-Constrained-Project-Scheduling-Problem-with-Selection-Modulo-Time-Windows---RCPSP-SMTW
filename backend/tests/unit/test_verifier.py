from helpers import block, mini_dataset, student

from curriculum_planner.analysis.context import build_context
from curriculum_planner.verify.plan_verifier import verify_plan

REG = {"min_credits_main": 6, "max_credits_main": 9, "max_main_terms": 8}


def _ctx():
    d = mini_dataset(
        [("A", 3, ["HK1"]), ("B", 3), ("C", 3), ("D", 3), ("X", 3), ("Y", 3)],
        [block("K", ["A", "B", "C", "D"], 12, rule="ALL_MANDATORY"), block("T", ["X", "Y"], 3)],
        deps=[("A", "B", "PREREQUISITE"), ("X", "Y", "MUTUALLY_EXCLUSIVE")],
        total=15,
        regulation=REG,
    )
    return build_context(d, student())


COUNTED = {"A": "K", "B": "K", "C": "K", "D": "K", "X": "T"}


def codes(ctx, a, counted=COUNTED):
    return {v.code for v in verify_plan(ctx, a, counted)}


def test_valid_plan_passes():
    ctx = _ctx()
    assert codes(ctx, {"A": 0, "C": 0, "B": 1, "D": 1, "X": 1}) == set()


def test_detects_each_violation():
    ctx = _ctx()
    assert "HC-04" in codes(ctx, {"A": 1, "C": 0, "B": 1, "D": 0, "X": 0})
    assert "HC-10" in codes(ctx, {"A": 1, "C": 0, "B": 2, "D": 0, "X": 2})
    assert "HC-08" in codes(ctx, {"A": 0, "C": 0, "D": 0, "X": 0, "B": 1})  # 12 TC > 9
    assert "HC-07" in codes(ctx, {"A": 0, "C": 0, "B": 1, "D": 1, "X": 1, "Y": 1}, {**COUNTED, "Y": "T"})
    assert "HC-03" in codes(
        ctx, {"A": 0, "C": 0, "B": 1, "X": 1}, {k: v for k, v in COUNTED.items() if k != "D"}
    )
    assert "HC-11" in codes(ctx, {"A": 0, "C": 0, "B": 1, "D": 1, "X": 30})
