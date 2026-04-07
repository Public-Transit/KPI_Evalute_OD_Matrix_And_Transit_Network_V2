import pytest

from src.config.app_config import ODAggregationConfig
from src.domain.service.aggregate.od_kpi_aggregator import ODKPIAggregator


def _build_trip_kpis(
    *,
    transfer_raw=0,
    circuity_raw=1.5,
    coverage_raw=0.25,
    transfer_score=100.0,
    circuity_score=66.66666666666667,
    service_coverage_score=25.0,
    composite_score=67.08333333333334,
):
    return {
        "transfer_kpi": {"score": transfer_raw},
        "circuity_kpi": {"score": circuity_raw},
        "spatial_coverage_kpi": {"score_ratio": coverage_raw},
        "composite_kpi": {
            "score": composite_score,
            "normalized_scores": {
                "transfer": transfer_score,
                "circuity": circuity_score,
                "service_coverage": service_coverage_score,
            },
        },
    }


def test_od_kpi_aggregator_calculates_expected_scores_for_multiple_valid_trips():
    aggregator = ODKPIAggregator()

    result = aggregator.calculate(
        [
            _build_trip_kpis(
                transfer_raw=0,
                transfer_score=100.0,
                circuity_score=66.66666666666667,
                service_coverage_score=25.0,
                composite_score=67.08333333333334,
            ),
            _build_trip_kpis(
                transfer_raw=1,
                transfer_score=66.66666666666667,
                circuity_score=66.66666666666667,
                service_coverage_score=25.0,
                composite_score=52.08333333333334,
            ),
        ]
    )

    assert result["transfer_kpi"]["score"] == pytest.approx(96.66666666666667)
    assert result["transfer_kpi"]["best_score"] == pytest.approx(100.0)
    assert result["transfer_kpi"]["weighted_average_score"] == pytest.approx(
        88.8888888888889
    )

    assert result["circuity_kpi"]["score"] == pytest.approx(66.66666666666667)
    assert result["circuity_kpi"]["best_score"] == pytest.approx(66.66666666666667)
    assert result["circuity_kpi"]["weighted_average_score"] == pytest.approx(
        66.66666666666667
    )

    assert result["spatial_coverage_kpi"]["score"] == pytest.approx(25.0)
    assert result["composite_kpi"]["score"] == pytest.approx(65.58333333333334)
    assert result["composite_kpi"]["best_score"] == pytest.approx(67.08333333333334)
    assert result["composite_kpi"]["weighted_average_score"] == pytest.approx(
        62.08333333333334
    )


def test_od_kpi_aggregator_filters_invalid_trips_by_hard_thresholds_and_missing_data():
    aggregator = ODKPIAggregator()
    valid_trip = _build_trip_kpis()

    result = aggregator.calculate(
        [
            valid_trip,
            _build_trip_kpis(transfer_raw=2),
            _build_trip_kpis(circuity_raw=2.6),
            _build_trip_kpis(coverage_raw=0.05),
            {
                "transfer_kpi": {"score": 0},
                "circuity_kpi": {"score": 1.5},
                "spatial_coverage_kpi": {"score_ratio": 0.25},
                "composite_kpi": {"score": None, "normalized_scores": {}},
            },
        ]
    )

    assert result["transfer_kpi"]["score"] == pytest.approx(valid_trip["composite_kpi"]["normalized_scores"]["transfer"])
    assert result["circuity_kpi"]["score"] == pytest.approx(valid_trip["composite_kpi"]["normalized_scores"]["circuity"])
    assert result["spatial_coverage_kpi"]["score"] == pytest.approx(valid_trip["composite_kpi"]["normalized_scores"]["service_coverage"])
    assert result["composite_kpi"]["score"] == pytest.approx(valid_trip["composite_kpi"]["score"])


def test_od_kpi_aggregator_uses_average_rank_for_ties_independent_of_input_order():
    aggregator = ODKPIAggregator()

    trip_scores = [
        _build_trip_kpis(
            transfer_score=100.0,
            circuity_score=90.0,
            service_coverage_score=60.0,
            composite_score=92.0,
        ),
        _build_trip_kpis(
            transfer_score=100.0,
            circuity_score=90.0,
            service_coverage_score=60.0,
            composite_score=92.0,
        ),
        _build_trip_kpis(
            transfer_score=50.0,
            circuity_score=40.0,
            service_coverage_score=20.0,
            composite_score=30.0,
        ),
    ]

    reordered_trip_scores = [trip_scores[2], trip_scores[0], trip_scores[1]]

    assert aggregator.calculate(trip_scores) == aggregator.calculate(reordered_trip_scores)


def test_od_kpi_aggregator_returns_invalid_when_no_trip_survives_filtering():
    aggregator = ODKPIAggregator()

    result = aggregator.calculate(
        [
            _build_trip_kpis(transfer_raw=2),
            _build_trip_kpis(circuity_raw=3.0),
            _build_trip_kpis(coverage_raw=0.0),
        ],
        min_valid_service_coverage_ratio=0.1,
    )

    for metric_name in (
        "transfer_kpi",
        "circuity_kpi",
        "spatial_coverage_kpi",
        "composite_kpi",
    ):
        metric_result = result[metric_name]
        assert metric_result["score"] is None
        assert metric_result["is_valid"] is False
        assert metric_result["reason"] == "No valid trips after hard-threshold filtering"
        assert metric_result["best_score"] is None
        assert metric_result["weighted_average_score"] is None


def test_od_kpi_aggregator_uses_constructor_config_as_default():
    aggregator = ODKPIAggregator(
        ODAggregationConfig(
            alpha=0.5,
            max_valid_transfer_count=2.0,
            max_valid_circuity=3.0,
            min_valid_service_coverage_ratio=0.2,
        )
    )

    result = aggregator.calculate(
        [
            _build_trip_kpis(
                transfer_raw=2,
                circuity_raw=2.8,
                coverage_raw=0.2,
                transfer_score=33.333333333333336,
                circuity_score=20.0,
                service_coverage_score=20.0,
                composite_score=25.0,
            ),
            _build_trip_kpis(
                transfer_raw=0,
                circuity_raw=1.2,
                coverage_raw=0.6,
                transfer_score=100.0,
                circuity_score=86.66666666666667,
                service_coverage_score=60.0,
                composite_score=84.0,
            ),
        ]
    )

    assert result["composite_kpi"]["score"] == pytest.approx(74.16666666666666)
    assert result["composite_kpi"]["parameters"]["alpha"] == pytest.approx(0.5)
