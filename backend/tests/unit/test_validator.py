from helpers import block, mini_dataset

from curriculum_planner.validation.validator import find_dependency_cycles, tarjan_scc, validate_dataset


def test_sample_dataset_has_no_errors(ds):
    report = validate_dataset(ds)
    assert report.ok, [i.message for i in report.errors]


def test_tarjan_finds_components():
    comps = tarjan_scc(["A", "B", "C", "D"], {"A": ["B"], "B": ["C"], "C": ["A"], "D": []})
    assert sorted(map(sorted, comps)) == [["A", "B", "C"], ["D"]]


def test_cycle_is_reported_as_data_error():
    """Trường hợp biên 4.1.1: chu trình A → B → C → A phải bị phát hiện trước khi vào solver."""
    d = mini_dataset(
        [("A", 3), ("B", 3), ("C", 3)],
        [block("K", ["A", "B", "C"], 9, rule="ALL_MANDATORY")],
        deps=[("A", "B", "PRE_COURSE"), ("B", "C", "PREREQUISITE"), ("C", "A", "PRE_COURSE")],
        total=9,
    )
    assert find_dependency_cycles(d) == [["A", "B", "C"]]
    report = validate_dataset(d)
    assert not report.ok
    assert any(i.code == "DV-04" for i in report.errors)


def test_two_way_corequisite_is_not_a_cycle():
    d = mini_dataset(
        [("A", 3), ("B", 3)],
        [block("K", ["A", "B"], 6, rule="ALL_MANDATORY")],
        deps=[("A", "B", "CO_REQUISITE"), ("B", "A", "CO_REQUISITE")],
        total=6,
    )
    assert find_dependency_cycles(d) == []


def test_block_impossible_and_unknown_reference():
    d = mini_dataset(
        [("A", 3)],
        [block("K", ["A", "X"], 9)],
        total=9,
    )
    codes = {i.code for i in validate_dataset(d).errors}
    assert {"DV-02", "DV-06"} <= codes
