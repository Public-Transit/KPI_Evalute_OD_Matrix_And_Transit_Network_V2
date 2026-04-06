import pytest

from src.entrypoints import api


def _fake_calculate_kpis_for_all_trips(*args, **kwargs):
    return [
        {
            "trip_id": "Trip_1",
            "summary": {
                "is_valid": True,
                "reason": None,
                "scores": {
                    "total_potential_demand": 120.0,
                },
            },
            "path": {
                "route_sequence": ["R1"],
                "stop_sequence": ["S2", "S3"],
            },
            "served_od_pairs": [
                {
                    "od_pair_id": "OD1",
                    "demand": 120.0,
                    "board_stop": "S2",
                    "alight_stop": "S3",
                }
            ],
        }
    ]


def test_calculate_kpi_all_routes_returns_concise_trip_schema(monkeypatch):
    monkeypatch.setattr(
        api.trip_kpi_services,
        "calculate_kpis_for_all_trips",
        _fake_calculate_kpis_for_all_trips,
    )

    payload = api.calculate_kpi_all_routes()

    assert payload["status"] == "success"
    assert len(payload["data"]) == 1

    first_trip = payload["data"][0]

    assert set(first_trip) == {"trip_id", "summary", "path", "served_od_pairs"}

    assert first_trip["summary"]["is_valid"] is True
    assert first_trip["summary"]["reason"] is None
    assert first_trip["summary"]["scores"]["total_potential_demand"] == pytest.approx(120.0)
    assert first_trip["path"]["route_sequence"] == ["R1"]
    assert first_trip["path"]["stop_sequence"] == ["S2", "S3"]
    assert first_trip["served_od_pairs"] == [
        {
            "od_pair_id": "OD1",
            "demand": 120.0,
            "board_stop": "S2",
            "alight_stop": "S3",
        }
    ]
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
