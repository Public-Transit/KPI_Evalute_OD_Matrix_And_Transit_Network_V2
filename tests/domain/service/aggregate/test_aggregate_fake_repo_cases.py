import pytest

from src.domain.service.aggregate.od_kpi_aggregator import ODKPIAggregator
from tests.domain.service.aggregate.aggregate_fake_repo_support import (
    AGGREGATE_CASES,
    run_aggregate_case,
)


def _case_result(case_id: str):
    case_definition = next(case for case in AGGREGATE_CASES if case.case_id == case_id)
    return run_aggregate_case(case_definition.repo_factory())


def test_ag1_excellent_direct_od_scores_high():
    result = _case_result("AG1")

    assert result["trip_count"] == 1
    option = result["option_results"][0]
    assert option["routes"] == ["R_DIRECT_GOOD"]
    assert option["transfer_kpi"]["score"] == 0
    assert option["composite_kpi"]["is_valid"] is True
    assert option["composite_kpi"]["score"] > 80.0
    assert result["aggregated_kpis"]["composite_kpi"]["score"] == pytest.approx(
        option["composite_kpi"]["score"]
    )


def test_ag2_weak_but_valid_od_scores_lower_than_ag1_and_remains_valid():
    ag1 = _case_result("AG1")
    ag2 = _case_result("AG2")

    assert ag2["trip_count"] == 1
    option = ag2["option_results"][0]
    assert option["routes"] == ["R_FEEDER", "R_TRUNK"]
    assert option["transfer_kpi"]["score"] == 1
    assert option["passed_hard_threshold"] is True
    assert ag2["aggregated_kpis"]["composite_kpi"]["is_valid"] is True
    assert (
        ag2["aggregated_kpis"]["composite_kpi"]["score"]
        < ag1["aggregated_kpis"]["composite_kpi"]["score"]
    )


def test_ag3_mixed_od_prefers_best_option_without_ignoring_weaker_option():
    result = _case_result("AG3")

    assert result["trip_count"] == 2
    assert result["valid_trip_count"] == 2

    trip_scores = [
        option_result["composite_kpi"]["score"] for option_result in result["option_results"]
    ]
    best_score = max(trip_scores)
    simple_average = sum(trip_scores) / len(trip_scores)
    od_score = result["aggregated_kpis"]["composite_kpi"]["score"]

    assert best_score > min(trip_scores)
    assert simple_average < od_score < best_score


def test_ag4_all_trips_filtered_out_returns_invalid_od_scores():
    result = _case_result("AG4")

    assert result["trip_count"] == 2
    assert result["valid_trip_count"] == 0

    for option_result in result["option_results"]:
        assert option_result["composite_kpi"]["is_valid"] is True
        assert option_result["passed_hard_threshold"] is False

    for metric_name in (
        "transfer_kpi",
        "circuity_kpi",
        "spatial_coverage_kpi",
        "composite_kpi",
    ):
        aggregated_metric = result["aggregated_kpis"][metric_name]
        assert aggregated_metric["score"] is None
        assert aggregated_metric["is_valid"] is False


def test_ag5_tie_stability_is_order_independent_and_keeps_two_best_scores_equal():
    result = _case_result("AG5")

    assert result["trip_count"] == 3
    assert result["valid_trip_count"] == 3

    sorted_option_scores = sorted(
        [option_result["composite_kpi"]["score"] for option_result in result["option_results"]],
        reverse=True,
    )
    assert sorted_option_scores[0] == pytest.approx(sorted_option_scores[1])
    assert sorted_option_scores[0] > sorted_option_scores[2]

    trip_kpi_results = [
        {
            "transfer_kpi": option_result["transfer_kpi"],
            "circuity_kpi": option_result["circuity_kpi"],
            "spatial_coverage_kpi": option_result["spatial_coverage_kpi"],
            "composite_kpi": option_result["composite_kpi"],
        }
        for option_result in result["option_results"]
    ]
    reversed_aggregated_result = ODKPIAggregator().calculate(
        list(reversed(trip_kpi_results))
    )

    assert result["aggregated_kpis"]["composite_kpi"]["score"] == pytest.approx(
        reversed_aggregated_result["composite_kpi"]["score"]
    )


def test_case_quality_order_matches_expected_good_to_bad_signal():
    ag1 = _case_result("AG1")
    ag2 = _case_result("AG2")
    ag3 = _case_result("AG3")
    ag5 = _case_result("AG5")

    scores = {
        "AG1": ag1["aggregated_kpis"]["composite_kpi"]["score"],
        "AG2": ag2["aggregated_kpis"]["composite_kpi"]["score"],
        "AG3": ag3["aggregated_kpis"]["composite_kpi"]["score"],
        "AG5": ag5["aggregated_kpis"]["composite_kpi"]["score"],
    }

    assert scores["AG1"] > scores["AG3"] > scores["AG2"]
    assert scores["AG5"] > scores["AG2"]
