import pytest

from src.domain.service.aggregate.composite_quality_index import (
    CompositeQualityIndexCalculator,
)


def test_composite_quality_index_returns_100_for_best_case():
    calc = CompositeQualityIndexCalculator()

    result = calc.calculate(0, 1.0, 1.0)

    assert result["is_valid"] is True
    assert result["reason"] is None
    assert result["invalid_inputs"] == {}
    assert result["normalized_scores"]["transfer"] == pytest.approx(100.0)
    assert result["normalized_scores"]["circuity"] == pytest.approx(100.0)
    assert result["normalized_scores"]["service_coverage"] == pytest.approx(100.0)
    assert result["score"] == pytest.approx(100.0)


def test_composite_quality_index_calculates_expected_weighted_score():
    calc = CompositeQualityIndexCalculator()

    result = calc.calculate(1, 1.3, 0.75)

    assert result["is_valid"] is True
    assert result["normalized_scores"]["transfer"] == pytest.approx(66.66666666666667)
    assert result["normalized_scores"]["circuity"] == pytest.approx(80.0)
    assert result["normalized_scores"]["service_coverage"] == pytest.approx(75.0)
    assert result["weighted_scores"]["transfer"] == pytest.approx(30.0)
    assert result["weighted_scores"]["circuity"] == pytest.approx(16.0)
    assert result["weighted_scores"]["service_coverage"] == pytest.approx(26.25)
    assert result["score"] == pytest.approx(72.25)


def test_composite_quality_index_clamps_out_of_range_scores():
    calc = CompositeQualityIndexCalculator()

    high_result = calc.calculate(3, 3.0, 1.2)
    low_result = calc.calculate(0, 1.0, -0.2)

    assert high_result["is_valid"] is True
    assert high_result["normalized_scores"]["transfer"] == pytest.approx(0.0)
    assert high_result["normalized_scores"]["circuity"] == pytest.approx(0.0)
    assert high_result["normalized_scores"]["service_coverage"] == pytest.approx(100.0)
    assert high_result["score"] == pytest.approx(35.0)

    assert low_result["is_valid"] is True
    assert low_result["normalized_scores"]["service_coverage"] == pytest.approx(0.0)
    assert low_result["score"] == pytest.approx(65.0)


def test_composite_quality_index_returns_invalid_when_any_input_is_invalid():
    calc = CompositeQualityIndexCalculator()

    result = calc.calculate("Not valid or >1", 1.3, 0.75)

    assert result["score"] is None
    assert result["is_valid"] is False
    assert result["reason"] is not None
    assert result["invalid_inputs"] == {
        "transfer_count": "Invalid KPI marker: Not valid or >1"
    }
    assert result["raw_inputs"]["transfer_count"] == "Not valid or >1"
    assert result["normalized_scores"]["transfer"] is None
    assert result["normalized_scores"]["circuity"] == pytest.approx(80.0)
    assert result["normalized_scores"]["service_coverage"] == pytest.approx(75.0)


def test_composite_quality_index_raises_for_invalid_configuration():
    calc = CompositeQualityIndexCalculator()

    with pytest.raises(ValueError):
        calc.calculate(0, 1.0, 1.0, transfer_max=0)

    with pytest.raises(ValueError):
        calc.calculate(0, 1.0, 1.0, circuity_max=1.0)
