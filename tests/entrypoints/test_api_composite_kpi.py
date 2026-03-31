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


class FakeRepoForApi:
    def get(self, reference_path: str):
        stops = [
            Stop("S1", 1.0, 1.0),
            Stop("S2", 2.0, 2.0),
        ]
        routes = [
            Route("R1", [Point(1.0, 1.0), Point(2.0, 2.0)], ["S1", "S2"]),
        ]
        zones = [
            Zone(
                "Z1",
                [Point(0.0, 0.0), Point(0.0, 2.0), Point(2.0, 2.0), Point(2.0, 0.0)],
                Point(1.0, 1.0),
            ),
            Zone(
                "Z2",
                [Point(1.0, 1.0), Point(1.0, 3.0), Point(3.0, 3.0), Point(3.0, 1.0)],
                Point(2.0, 2.0),
            ),
        ]
        od_pairs = [ODPair("OD1", "Z1", "Z2", 10)]
        trips = []
        return stops, routes, zones, od_pairs, trips


def _fake_batch_route_all_od_pairs(*args, **kwargs):
    option = EvaluatedRoutingOption(
        CandidateTrip([CandidateLeg("R1", {"S1"}, {"S2"})]),
        Trip([Leg("R1", "S1", "S2")]),
    )
    return [ODRoutingResultV2("OD1", [option])]


def test_calculate_kpi_all_od_pairs_returns_composite_kpi(monkeypatch):
    monkeypatch.setattr(api, "FakeRepoL5", FakeRepoForApi)
    monkeypatch.setattr(api, "ShapelyGeometryCalculator", MockGeometryCalculator)
    monkeypatch.setattr(api.routing_services, "batch_route_all_od_pairs", _fake_batch_route_all_od_pairs)

    payload = api.calculate_kpi_all_od_pairs()

    assert payload["status"] == "success"
    option = payload["data"][0]["options"][0]
    kpis = option["kpis"]

    assert "transfer_kpi" in kpis
    assert "circuity_kpi" in kpis
    assert "spatial_coverage_kpi" in kpis
    assert "composite_kpi" in kpis

    composite_kpi = kpis["composite_kpi"]
    assert composite_kpi["is_valid"] is True
    assert composite_kpi["score"] == pytest.approx(
        composite_kpi["weighted_scores"]["transfer"]
        + composite_kpi["weighted_scores"]["circuity"]
        + composite_kpi["weighted_scores"]["service_coverage"]
    )
    assert composite_kpi["raw_inputs"]["transfer_count"] == kpis["transfer_kpi"]["score"]
    assert composite_kpi["raw_inputs"]["circuity_index"] == kpis["circuity_kpi"]["score"]
    assert composite_kpi["raw_inputs"]["service_coverage_ratio"] == kpis["spatial_coverage_kpi"]["score_ratio"]
