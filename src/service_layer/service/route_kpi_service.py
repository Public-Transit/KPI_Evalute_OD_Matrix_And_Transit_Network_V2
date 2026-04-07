from numbers import Real

from src.domain.port import IGeometryCalculator
from src.domain.service.filter import AbstractCandidateTripFilterV2
from src.domain.service.generate_od_routing_result import GenerateODRoutingResultService
from src.domain.service.routing import AbstractRouting
from src.domain.service.trip_kpi_caculator.trip_kpi_base import TripKPICalculator
from src.domain.service.spatial import reverse_route_to_trip
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.service_layer.unit_of_work import AbstractUnitOfWork

def calculate_kpis_for_all_routes(
    kpi_calculators: list[TripKPICalculator],
    uow: AbstractUnitOfWork,
    routing_engine: AbstractRouting,
    geometry_calculator: IGeometryCalculator,
    reference_path: str
) -> list[dict]:
    """
    Service layer function to calculate KPIs for all routes in the repository.
    """
    with uow:
        # FakeRepoGrid3x3.get() returns (stops, routes, zones, od_pairs) - only 4 values.
        stops, routes, zones, od_pairs = uow.repo.get(reference_path)
        transit_network = TransitNetwork(stops, routes)
        od_matrix = ODMatrix(od_pairs, zones)
        
        routes_by_trip_form = reverse_route_to_trip(routes)
        
        results = []

        for trip in routes_by_trip_form:
            trip_results = {
                "route_ids": [leg.route_id for leg in trip.legs],
                "stops": [leg.board_stop_id for leg in trip.legs] + [trip.legs[-1].alight_stop_id],
                "kpis": {}
            }
            for calculator in kpi_calculators:
                kpi_name = calculator.__class__.__name__
                value = calculator.calculate(
                    trip,
                    transit_network,
                    od_matrix,
                    routing_engine,
                    geometry_calculator
                )
                trip_results["kpis"][kpi_name] = value
            
            results.append(trip_results)
        
    return results
