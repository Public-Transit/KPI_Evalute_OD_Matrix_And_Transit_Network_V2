# src/entrypoints/api.py
from numbers import Real
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator
from src.adapters.repository.fake_repo_grid_3x3 import FakeRepoGrid3x3
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.domain.service.aggregate.composite_quality_index import (
    CompositeQualityIndexCalculator,
)
from src.domain.service.aggregate.od_kpi_aggregator import ODKPIAggregator
from src.domain.service.filter import MinDistanceCandidateTripFilterV2
from src.domain.service.kpi_caculator.circuity_kpi import CircuityIndexCalculator
from src.domain.service.kpi_caculator.spatial_coverage_kpi import (
    SpatialCoverageCalculator,
)
from src.domain.service.kpi_caculator.transfer_kpi import TransferRateCalculator
from src.domain.service.routing import CombinedRoutingEngine
from src.domain.service.trip_kpi_caculator.total_potential_demand_in_trip import (
    TotalPotentialDemandInTripCalculator,
)
from src.service_layer.service import routing_services, trip_kpi_services
from src.service_layer.unit_of_work import DummyUnitOfWork


app = FastAPI(
    title="Transit Network KPI API",
    description="API dinh tuyen va danh gia KPI mang luoi giao thong",
)


class RouteUpdateRequest(BaseModel):
    new_stops: list[str]


class SummaryScoresResponse(BaseModel):
    composite: float | None = Field(
        ..., description="OD-level composite score on a 0-100 scale."
    )
    transfer: float | None = Field(
        ..., description="OD-level transfer score normalized to 0-100."
    )
    circuity: float | None = Field(
        ..., description="OD-level circuity score normalized to 0-100."
    )
    spatial_coverage: float | None = Field(
        ..., description="OD-level spatial coverage score normalized to 0-100."
    )


class SummaryResponse(BaseModel):
    is_valid: bool = Field(
        ..., description="Whether the OD-level summary could be calculated."
    )
    reason: str | None = Field(
        ..., description="Reason returned when the OD-level summary is invalid."
    )
    scores: SummaryScoresResponse


class RoutePathResponse(BaseModel):
    route_sequence: list[str] = Field(
        ..., description="Representative route sequence for this option."
    )
    stop_sequence: list[str] = Field(
        ..., description="Representative stop sequence for this option."
    )


class RouteMetricsResponse(BaseModel):
    composite_score: float | None = Field(
        ..., description="Composite score for the route option."
    )
    transfer_count: int | None = Field(
        ..., description="Raw transfer count for the route option."
    )
    circuity_index: float | None = Field(
        ..., description="Raw circuity index for the route option."
    )
    coverage_ratio: float | None = Field(
        ..., description="Raw spatial coverage ratio for the route option."
    )


class RouteOptionResponse(BaseModel):
    option_id: str = Field(..., description="Stable display identifier after sorting.")
    path: RoutePathResponse
    metrics: RouteMetricsResponse


class ODKPIResultResponse(BaseModel):
    od_pair_id: str = Field(..., description="Identifier of the OD pair.")
    summary: SummaryResponse
    route_options: list[RouteOptionResponse]


class CalculateAllKPIResponse(BaseModel):
    status: Literal["success"] = Field(
        ..., description="Processing status of the API response."
    )
    data: list[ODKPIResultResponse]

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "data": [
                    {
                        "od_pair_id": "OD1",
                        "summary": {
                            "is_valid": True,
                            "reason": None,
                            "scores": {
                                "composite": 46.75,
                                "transfer": 66.66666666666667,
                                "circuity": 40.0,
                                "spatial_coverage": 25.0,
                            },
                        },
                        "route_options": [
                            {
                                "option_id": "OPT1",
                                "path": {
                                    "route_sequence": ["R1"],
                                    "stop_sequence": ["S1", "S3"],
                                },
                                "metrics": {
                                    "composite_score": 67.08333333333334,
                                    "transfer_count": 0,
                                    "circuity_index": 1.2,
                                    "coverage_ratio": 0.25,
                                },
                            }
                        ],
                    }
                ],
            }
        }
    }


class TripSummaryScoresResponse(BaseModel):
    total_potential_demand: float | None = Field(
        ..., description="Total potential OD demand served by this trip."
    )


class TripSummaryResponse(BaseModel):
    is_valid: bool = Field(
        ..., description="Whether the trip-level summary could be calculated."
    )
    reason: str | None = Field(
        ..., description="Reason returned when the trip-level summary is invalid."
    )
    scores: TripSummaryScoresResponse


class ServedODPairResponse(BaseModel):
    od_pair_id: str
    demand: float
    board_stop: str
    alight_stop: str


class TripKPIResultResponse(BaseModel):
    trip_id: str
    summary: TripSummaryResponse
    path: RoutePathResponse
    served_od_pairs: list[ServedODPairResponse]


class CalculateAllRoutesKPIResponse(BaseModel):
    status: Literal["success"] = Field(
        ..., description="Processing status of the API response."
    )
    data: list[TripKPIResultResponse]

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "data": [
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
                            "stop_sequence": ["S1", "S4"],
                        },
                        "served_od_pairs": [
                            {
                                "od_pair_id": "OD1",
                                "demand": 120.0,
                                "board_stop": "S1",
                                "alight_stop": "S4",
                            }
                        ],
                    }
                ],
            }
        }
    }


DEFAULT_REFERENCE_PATH = "path/to/data/matsim"


def _coerce_metric_value(value):
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    return value


def _coerce_transfer_count(value):
    numeric_value = _coerce_metric_value(value)
    if numeric_value is None:
        return None
    if float(numeric_value).is_integer():
        return int(numeric_value)
    return None


def _build_summary(aggregated_kpis: dict) -> dict:
    composite_kpi = aggregated_kpis["composite_kpi"]
    return {
        "is_valid": composite_kpi["is_valid"],
        "reason": composite_kpi["reason"],
        "scores": {
            "composite": aggregated_kpis["composite_kpi"]["score"],
            "transfer": aggregated_kpis["transfer_kpi"]["score"],
            "circuity": aggregated_kpis["circuity_kpi"]["score"],
            "spatial_coverage": aggregated_kpis["spatial_coverage_kpi"]["score"],
        },
    }


def _build_path_payload(evaluated_option) -> dict:
    representative_trip = evaluated_option.representative_trip()
    if not representative_trip or not representative_trip.legs:
        return {
            "route_sequence": [],
            "stop_sequence": [],
        }

    return {
        "route_sequence": [leg.route_id for leg in representative_trip.legs],
        "stop_sequence": [leg.board_stop_id for leg in representative_trip.legs]
        + [representative_trip.legs[-1].alight_stop_id],
    }


def _route_option_sort_key(route_option: dict) -> tuple[bool, float]:
    composite_score = route_option["metrics"]["composite_score"]
    if composite_score is None:
        return True, 0.0
    return False, -float(composite_score)


def _sort_and_number_route_options(route_options: list[dict]) -> list[dict]:
    sorted_route_options = sorted(route_options, key=_route_option_sort_key)
    return [
        {
            "option_id": f"OPT{index}",
            "path": route_option["path"],
            "metrics": route_option["metrics"],
        }
        for index, route_option in enumerate(sorted_route_options, start=1)
    ]


@app.post(
    "/api/kpi/calculate-all",
    response_model=CalculateAllKPIResponse,
    summary="Calculate KPI summary for all OD pairs",
    response_description="Concise OD KPI results grouped by OD pair.",
)
def calculate_kpi_all_od_pairs() -> CalculateAllKPIResponse:
    """
    Calculate concise KPI results for all OD pairs.
    """
    repo = FakeRepoGrid3x3()
    uow = DummyUnitOfWork(repo)
    routing_engine = CombinedRoutingEngine()
    filter_engine = MinDistanceCandidateTripFilterV2()
    geo_calc = ShapelyGeometryCalculator()

    try:
        results = routing_services.batch_route_all_od_pairs(
            routing_engine,
            filter_engine,
            uow,
            geo_calc,
            DEFAULT_REFERENCE_PATH,
        )

        stops, routes, zones, od_pairs, trips = uow.repo.get(DEFAULT_REFERENCE_PATH)
        transit_network = TransitNetwork(stops, routes)
        od_matrix = ODMatrix(od_pairs, zones)

        transfer_calc = TransferRateCalculator()
        circuity_calc = CircuityIndexCalculator()
        spatial_calc = SpatialCoverageCalculator()
        composite_calc = CompositeQualityIndexCalculator()
        od_aggregator = ODKPIAggregator()

        json_results = []
        for routing_result in results:
            route_options_data = []
            trip_kpi_results = []

            for evaluated_option in routing_result.evaluated_routing_options():
                transfer_result = transfer_calc.calculate(evaluated_option)
                circuity_result = circuity_calc.calculate(
                    evaluated_option,
                    transit_network=transit_network,
                    geometry_calculator=geo_calc,
                )
                spatial_result = spatial_calc.calculate(
                    evaluated_option,
                    od_pair_id=routing_result.od_pair_id(),
                    od_matrix=od_matrix,
                    transit_network=transit_network,
                    geometry_calculator=geo_calc,
                )
                composite_result = composite_calc.calculate(
                    transfer_result.get("score"),
                    circuity_result.get("score"),
                    spatial_result.get("score_ratio"),
                )

                option_kpis = {
                    "transfer_kpi": transfer_result,
                    "circuity_kpi": circuity_result,
                    "spatial_coverage_kpi": spatial_result,
                    "composite_kpi": composite_result,
                }
                trip_kpi_results.append(option_kpis)

                route_options_data.append(
                    {
                        "path": _build_path_payload(evaluated_option),
                        "metrics": {
                            "composite_score": _coerce_metric_value(
                                composite_result.get("score")
                            ),
                            "transfer_count": _coerce_transfer_count(
                                transfer_result.get("score")
                            ),
                            "circuity_index": _coerce_metric_value(
                                circuity_result.get("score")
                            ),
                            "coverage_ratio": _coerce_metric_value(
                                spatial_result.get("score_ratio")
                            ),
                        },
                    }
                )

            aggregated_kpis = od_aggregator.calculate(trip_kpi_results)

            json_results.append(
                {
                    "od_pair_id": routing_result.od_pair_id(),
                    "summary": _build_summary(aggregated_kpis),
                    "route_options": _sort_and_number_route_options(route_options_data),
                }
            )

        return {"status": "success", "data": json_results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post(
    "/api/kpi/calculate-all-routes",
    response_model=CalculateAllRoutesKPIResponse,
    summary="Calculate KPI summary for all trips",
    response_description="Concise trip-level KPI results grouped by trip.",
)
def calculate_kpi_all_routes() -> CalculateAllRoutesKPIResponse:
    """
    Calculate concise trip-level KPI results for all trips.
    """
    repo = FakeRepoGrid3x3()
    uow = DummyUnitOfWork(repo)
    routing_engine = CombinedRoutingEngine()
    geo_calc = ShapelyGeometryCalculator()

    try:
        results = trip_kpi_services.calculate_kpis_for_all_trips(
            [TotalPotentialDemandInTripCalculator()],
            uow,
            routing_engine,
            geo_calc,
            DEFAULT_REFERENCE_PATH,
        )
        return {"status": "success", "data": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
