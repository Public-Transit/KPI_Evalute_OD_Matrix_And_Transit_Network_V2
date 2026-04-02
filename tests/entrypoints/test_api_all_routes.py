import pytest

from src.entrypoints import api


def test_calculate_kpi_all_routes_returns_concise_trip_schema():
    payload = api.calculate_kpi_all_routes()

    assert payload["status"] == "success"
    assert len(payload["data"]) == 2

    first_trip = payload["data"][0]
    second_trip = payload["data"][1]

    assert set(first_trip) == {"trip_id", "summary", "path", "served_od_pairs"}
    assert set(second_trip) == {"trip_id", "summary", "path", "served_od_pairs"}

    assert first_trip["summary"]["is_valid"] is True
    assert first_trip["summary"]["reason"] is None
    assert first_trip["summary"]["scores"]["total_potential_demand"] == pytest.approx(120.0)
    assert first_trip["path"]["route_sequence"] == ["R1"]
    assert first_trip["path"]["stop_sequence"] == ["S1", "S4"]
    assert first_trip["served_od_pairs"] == [
        {
            "od_pair_id": "OD1",
            "demand": 120.0,
            "board_stop": "S1",
            "alight_stop": "S4",
        }
    ]

    assert second_trip["summary"]["is_valid"] is True
    assert second_trip["summary"]["reason"] is None
    assert second_trip["summary"]["scores"]["total_potential_demand"] == pytest.approx(0.0)
    assert second_trip["path"]["route_sequence"] == ["R2"]
    assert second_trip["path"]["stop_sequence"] == ["S3", "S5"]
    assert second_trip["served_od_pairs"] == []

    assert (
        first_trip["summary"]["scores"]["total_potential_demand"]
        > second_trip["summary"]["scores"]["total_potential_demand"]
    )
    assert "route_ids" not in first_trip
    assert "stops" not in first_trip
    assert "kpis" not in first_trip


def test_openapi_declares_concise_route_response_contract():
    openapi_schema = api.app.openapi()

    response_schema = openapi_schema["paths"]["/api/kpi/calculate-all-routes"]["post"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"]
    components = openapi_schema["components"]["schemas"]

    assert response_schema == {"$ref": "#/components/schemas/CalculateAllRoutesKPIResponse"}
    assert set(components["TripKPIResultResponse"]["properties"]) == {
        "trip_id",
        "summary",
        "path",
        "served_od_pairs",
    }
    assert set(components["TripSummaryScoresResponse"]["properties"]) == {
        "total_potential_demand",
    }
