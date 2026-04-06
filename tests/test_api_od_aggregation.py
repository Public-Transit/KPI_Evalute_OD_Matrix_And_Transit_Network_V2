import pytest

from src.domain.model.leg import CandidateLeg, Leg
from src.domain.model.od_pair import ODPair
from src.domain.model.point import Point
from src.domain.model.route import Route
from src.domain.model.routing_result import EvaluatedRoutingOption, ODRoutingResultV2
from src.domain.model.stop import Stop
from src.domain.model.trip import CandidateTrip, Trip
from src.domain.model.zone import Zone
from src.entrypoints import api
from tests.domain.mock_geometry import MockGeometryCalculator


class FakeRepoForODAggregationApi:
    def get(self, reference_path: str):
        stops = [
            Stop("S1", 1.0, 1.0),
            Stop("S2", 2.0, 2.0),
            Stop("S3", 3.0, 3.0),
        ]
        routes = [
            Route(
                "R1",
                [Point(1.0, 1.0), Point(2.0, 2.0), Point(3.0, 3.0)],
                ["S1", "S2", "S3"],
            ),
            Route("R2", [Point(2.0, 2.0), Point(3.0, 3.0)], ["S2", "S3"]),
        ]
        zones = [
            Zone(
                "Z1",
                [Point(0.0, 0.0), Point(0.0, 2.0), Point(2.0, 2.0), Point(2.0, 0.0)],
                Point(1.0, 1.0),
            ),
            Zone(
                "Z2",
                [Point(2.0, 2.0), Point(2.0, 4.0), Point(4.0, 4.0), Point(4.0, 2.0)],
                Point(3.0, 3.0),
            ),
        ]
        od_pairs = [ODPair("OD1", "Z1", "Z2", 10)]
        return stops, routes, zones, od_pairs


def _fake_batch_route_all_od_pairs(*args, **kwargs):
    direct_option = EvaluatedRoutingOption(
        CandidateTrip([CandidateLeg("R1", {"S1"}, {"S3"})]),
        Trip([Leg("R1", "S1", "S3")]),
    )
    one_transfer_option = EvaluatedRoutingOption(
        CandidateTrip(
            [
                CandidateLeg("R1", {"S1"}, {"S2"}),
                CandidateLeg("R2", {"S2"}, {"S3"}),
            ]
        ),
        Trip([Leg("R1", "S1", "S2"), Leg("R2", "S2", "S3")]),
    )
    return [ODRoutingResultV2("OD1", [one_transfer_option, direct_option])]


def test_calculate_kpi_all_od_pairs_returns_summary_and_sorted_route_options(monkeypatch):
    monkeypatch.setattr(api, "FakeRepoGrid3x3", FakeRepoForODAggregationApi)
    monkeypatch.setattr(api, "ShapelyGeometryCalculator", MockGeometryCalculator)
    monkeypatch.setattr(
        api.routing_services,
        "batch_route_all_od_pairs",
        _fake_batch_route_all_od_pairs,
    )

    payload = api.calculate_kpi_all_od_pairs()

    assert payload["status"] == "success"
    od_result = payload["data"][0]
    assert od_result["od_pair_id"] == "OD1"
    assert "aggregated_kpis" not in od_result
    assert "options" not in od_result
    assert len(od_result["route_options"]) == 2

    summary = od_result["summary"]
    route_options = od_result["route_options"]

    assert summary["is_valid"] is True
    assert summary["reason"] is None
    assert summary["scores"]["transfer"] == pytest.approx(96.66666666666667)
    assert summary["scores"]["circuity"] == pytest.approx(66.66666666666667)
    assert summary["scores"]["spatial_coverage"] == pytest.approx(50.0)
    assert summary["scores"]["composite"] == pytest.approx(74.33333333333333)

    assert [option["option_id"] for option in route_options] == ["OPT1", "OPT2"]
    assert route_options[0]["metrics"]["composite_score"] == pytest.approx(75.83333333333333)
    assert route_options[1]["metrics"]["composite_score"] == pytest.approx(60.833333333333336)
    assert route_options[0]["metrics"]["transfer_count"] == 0
    assert route_options[1]["metrics"]["transfer_count"] == 1
    assert route_options[0]["path"]["route_sequence"] == ["R1"]
    assert route_options[0]["path"]["stop_sequence"] == ["S1", "S3"]
    assert route_options[1]["path"]["route_sequence"] == ["R1", "R2"]
    assert route_options[1]["path"]["stop_sequence"] == ["S1", "S2", "S3"]
    assert route_options[0]["metrics"]["composite_score"] > route_options[1]["metrics"]["composite_score"]

    for option in route_options:
        assert "candidate_routes" not in option
        assert "representative_trip" not in option
        assert set(option["metrics"]) == {
            "composite_score",
            "transfer_count",
            "circuity_index",
            "coverage_ratio",
        }
