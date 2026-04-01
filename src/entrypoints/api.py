# src/entrypoints/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator
from src.adapters.repository.fake_repo_f1 import FakeRepoF1
from src.adapters.repository.fake_repo_f2 import FakeRepoF2
from src.adapters.repository.fake_repo_f3 import FakeRepoF3
from src.adapters.repository.fake_repo_f4 import FakeRepoF4
from src.adapters.repository.fake_repo_f5 import FakeRepoF5
from src.adapters.repository.fake_repo_l1 import FakeRepoL1
from src.adapters.repository.fake_repo_l2 import FakeRepoL2
from src.adapters.repository.fake_repo_l3 import FakeRepoL3
from src.adapters.repository.fake_repo_l4 import FakeRepoL4
from src.adapters.repository.fake_repo_l5 import FakeRepoL5
from src.adapters.repository.fake_reapository import FakeRepository
from src.adapters.repository.visualize_zone_and_transitnetwork import (
    VisualizeZoneAndTransitNetwork,
)
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
from src.service_layer.service import routing_services
from src.service_layer.unit_of_work import DummyUnitOfWork


app = FastAPI(
    title="Transit Network KPI API",
    description="API dinh tuyen va danh gia KPI mang luoi giao thong",
)


class RouteUpdateRequest(BaseModel):
    new_stops: list[str]


DEFAULT_REFERENCE_PATH = "path/to/data/matsim"


@app.post("/api/kpi/calculate-all")
def calculate_kpi_all_od_pairs():
    """
    Calculate all KPIs after generating routing options for all OD pairs.
    """
    repo = FakeRepoL5()
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
            options_data = []
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

                candidate_trip = evaluated_option.candidate_trip()
                candidate_routes = (
                    [leg.route_id for leg in candidate_trip.candidate_legs]
                    if candidate_trip and candidate_trip.candidate_legs
                    else []
                )

                representative_trip = evaluated_option.representative_trip()
                if representative_trip and representative_trip.legs:
                    representative_routes = [
                        leg.route_id for leg in representative_trip.legs
                    ]
                    representative_stops = [
                        leg.board_stop_id for leg in representative_trip.legs
                    ] + [representative_trip.legs[-1].alight_stop_id]
                else:
                    representative_routes = []
                    representative_stops = []

                options_data.append(
                    {
                        "candidate_routes": candidate_routes,
                        "representative_trip": {
                            "routes": representative_routes,
                            "stops": representative_stops,
                        },
                        "kpis": option_kpis,
                    }
                )

            aggregated_kpis = od_aggregator.calculate(trip_kpi_results)

            json_results.append(
                {
                    "od_pair": routing_result.od_pair_id(),
                    "aggregated_kpis": aggregated_kpis,
                    "options": options_data,
                }
            )

        return {"status": "success", "data": json_results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
