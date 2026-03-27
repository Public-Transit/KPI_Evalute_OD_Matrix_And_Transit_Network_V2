# src/service_layer/service/routing_services.py
from src.service_layer.unit_of_work import AbstractUnitOfWork
from src.domain.service.routing import AbstractRouting

from src.domain.model.route import Route
from src.domain.model.transit_network import TransitNetwork
from src.domain.port import IGeometryCalculator
from src.domain.model.od_matrix import ODMatrix

from src.domain.service.filter import AbstractCandidateTripFilterV2
from src.domain.model.routing_result import ODRoutingResultV2
from src.domain.service.generate_od_routing_result import GenerateODRoutingResultService


def batch_route_all_od_pairs(routing_engine: AbstractRouting, filter_engine: AbstractCandidateTripFilterV2, uow: AbstractUnitOfWork, geo_calc: IGeometryCalculator, reference_path: str) -> list[ODRoutingResultV2]:
    """
    Tính toán KPI của tất cả các cặp OD và trả ra kết quả class ODRoutingResultV2
    """
    with uow:
        # Lấy data từ Repo
        stops, routes, zones, od_pairs, trips = uow.repo.get(reference_path)
        transit_network = TransitNetwork(stops, routes)
        od_matrix = ODMatrix(od_pairs, zones)
        
        service = GenerateODRoutingResultService(routing_engine, filter_engine)
        return service.generate_od_routing_result(od_matrix, transit_network, geo_calc)
