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


class LowCoverageGeometryCalculator(MockGeometryCalculator):
    def calculate_zone_coverage_ratio(self, zone, points, radius_m):
        return 0.1


def test_calculate_kpi_all_od_pairs_returns_concise_single_option_schema(monkeypatch):
    monkeypatch.setattr(api, "FakeRepoGrid3x3", FakeRepoForApi)
    monkeypatch.setattr(api, "ShapelyGeometryCalculator", MockGeometryCalculator)
    monkeypatch.setattr(api.routing_services, "batch_route_all_od_pairs", _fake_batch_route_all_od_pairs)

    payload = api.calculate_kpi_all_od_pairs()

    assert payload["status"] == "success"
    od_result = payload["data"][0]
    option = od_result["route_options"][0]
    summary = od_result["summary"]

    assert set(od_result) == {"od_pair_id", "summary", "route_options"}
    assert od_result["od_pair_id"] == "OD1"
    assert summary["is_valid"] is True
    assert summary["reason"] is None
    assert set(summary["scores"]) == {
        "composite",
        "transfer",
        "circuity",
        "spatial_coverage",
    }

    assert option["option_id"] == "OPT1"
    assert option["path"]["route_sequence"] == ["R1"]
    assert option["path"]["stop_sequence"] == ["S1", "S2"]
    assert option["metrics"]["transfer_count"] == 0
    assert option["metrics"]["circuity_index"] == pytest.approx(1.5)
    assert option["metrics"]["coverage_ratio"] == pytest.approx(0.25)
    assert option["metrics"]["composite_score"] == pytest.approx(summary["scores"]["composite"])

    assert "aggregated_kpis" not in od_result
    assert "options" not in od_result
    assert "candidate_routes" not in option
    assert "representative_trip" not in option
    assert "best_score" not in summary
    assert "weighted_average_score" not in summary


def test_calculate_kpi_all_od_pairs_returns_invalid_summary_when_all_options_filtered(
    monkeypatch,
):
    monkeypatch.setattr(api, "FakeRepoGrid3x3", FakeRepoForApi)
    monkeypatch.setattr(api, "ShapelyGeometryCalculator", LowCoverageGeometryCalculator)
    monkeypatch.setattr(api.routing_services, "batch_route_all_od_pairs", _fake_batch_route_all_od_pairs)

    payload = api.calculate_kpi_all_od_pairs()

    assert payload["status"] == "success"
    od_result = payload["data"][0]
    summary = od_result["summary"]
    option = od_result["route_options"][0]

    assert summary["is_valid"] is False
    assert summary["reason"] == "No valid trips after hard-threshold filtering"
    assert summary["scores"] == {
        "composite": None,
        "transfer": None,
        "circuity": None,
        "spatial_coverage": None,
    }
    assert option["option_id"] == "OPT1"
    assert option["path"]["route_sequence"] == ["R1"]
    assert option["metrics"]["transfer_count"] == 0
    assert option["metrics"]["circuity_index"] == pytest.approx(1.5)
    assert option["metrics"]["coverage_ratio"] == pytest.approx(0.01)
    assert option["metrics"]["composite_score"] is not None


def test_openapi_declares_concise_response_contract():
    openapi_schema = api.app.openapi()

    response_schema = openapi_schema["paths"]["/api/kpi/calculate-all"]["post"]["responses"][
        "200"
    ]["content"]["application/json"]["schema"]
    components = openapi_schema["components"]["schemas"]

    assert response_schema == {"$ref": "#/components/schemas/CalculateAllKPIResponse"}
    assert set(components["ODKPIResultResponse"]["properties"]) == {
        "od_pair_id",
        "summary",
        "route_options",
    }
    assert set(components["SummaryScoresResponse"]["properties"]) == {
        "composite",
        "transfer",
        "circuity",
        "spatial_coverage",
    }
    assert set(components["RouteMetricsResponse"]["properties"]) == {
        "composite_score",
        "transfer_count",
        "circuity_index",
        "coverage_ratio",
    }
