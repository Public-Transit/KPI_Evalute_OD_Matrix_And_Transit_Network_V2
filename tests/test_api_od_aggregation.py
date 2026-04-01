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
        trips = []
        return stops, routes, zones, od_pairs, trips


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
    return [ODRoutingResultV2("OD1", [direct_option, one_transfer_option])]


def test_calculate_kpi_all_od_pairs_returns_aggregated_kpis(monkeypatch):
    monkeypatch.setattr(api, "FakeRepoL5", FakeRepoForODAggregationApi)
    monkeypatch.setattr(api, "ShapelyGeometryCalculator", MockGeometryCalculator)
    monkeypatch.setattr(
        api.routing_services,
        "batch_route_all_od_pairs",
        _fake_batch_route_all_od_pairs,
    )

    payload = api.calculate_kpi_all_od_pairs()

    assert payload["status"] == "success"
    od_result = payload["data"][0]
    assert "aggregated_kpis" in od_result
    assert len(od_result["options"]) == 2

    aggregated_kpis = od_result["aggregated_kpis"]
    option_kpis = [option["kpis"] for option in od_result["options"]]

    assert aggregated_kpis["transfer_kpi"]["score"] == pytest.approx(96.66666666666667)
    assert aggregated_kpis["circuity_kpi"]["score"] == pytest.approx(66.66666666666667)
    assert aggregated_kpis["spatial_coverage_kpi"]["score"] == pytest.approx(25.0)
    assert aggregated_kpis["composite_kpi"]["score"] == pytest.approx(65.58333333333334)

    assert option_kpis[0]["composite_kpi"]["score"] == pytest.approx(67.08333333333334)
    assert option_kpis[1]["composite_kpi"]["score"] == pytest.approx(52.083333333333336)
    assert aggregated_kpis["composite_kpi"]["best_score"] == pytest.approx(
        max(option["composite_kpi"]["score"] for option in option_kpis)
    )
