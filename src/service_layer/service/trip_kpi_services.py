# src/service_layer/service/trip_kpi_services.py
from src.service_layer.unit_of_work import AbstractUnitOfWork
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.od_matrix import ODMatrix
from src.domain.service.trip_kpi_caculator.trip_kpi_base import TripKPICalculator
from src.domain.port import IGeometryCalculator
from src.domain.service.routing import AbstractRouting

def calculate_kpis_for_all_trips(
    kpi_calculators: list[TripKPICalculator],
    uow: AbstractUnitOfWork,
    routing_engine: AbstractRouting,
    geometry_calculator: IGeometryCalculator,
    reference_path: str
) -> list[dict]:
    """
    Service layer function to calculate KPIs for all trips in the repository.
    """
    with uow:
        stops, routes, zones, od_pairs, trips = uow.repo.get(reference_path)
        transit_network = TransitNetwork(stops, routes)
        od_matrix = ODMatrix(od_pairs, zones)
        
        results = []
        for index, trip in enumerate(trips):
            trip_results = {
                "trip_id": f"Trip_{index + 1}",
                "route_ids": [leg.route_id for leg in trip.legs],
                "stops": [leg.board_stop_id for leg in trip.legs] + [trip.legs[-1].alight_stop_id],
                "kpis": {}
            }
            
            for calculator in kpi_calculators:
                # Assuming the calculator class name or a descriptive name can be used as key
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
