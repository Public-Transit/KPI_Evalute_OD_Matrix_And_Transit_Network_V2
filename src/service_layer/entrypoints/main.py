from src.domain.model.transit_network import TransitNetwork
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.routing_result import ODRoutingResult
from src.domain.service.routing import OneTransferRoutingEngine
from src.service_layer.unit_of_work import DummyUnitOfWork
from src.adapters.repository.abstract_repository import AbstractRepository # Assume implemented
from src.service_layer.service import routing_services

def api_calculate_kpi_all_od_pairs():
    """
    Entrypoint: FastAPI route hoặc CLI command.
    Chịu trách nhiệm nhận request, cấu hình UoW, gọi Application Service và trả về JSON.
    """
    repo = AbstractRepository()
    uow = DummyUnitOfWork(repo)
    routing_engine = OneTransferRoutingEngine()
    
    reference_path = "path/to/data/matsim"
    # Delegate toàn bộ work cho Application Service
    od_routing_results = routing_services.batch_route_all_od_pairs(routing_engine, uow, reference_path)
    
    return [result.__dict__ for result in od_routing_results] # Format to JSON

def api_preview_change_route(route_id: str, new_stops: list[str]):
    """
    Entrypoint: Preview thay đổi tuyến.
    """
    uow = DummyUnitOfWork(AbstractRepository())
    routing_engine = OneTransferRoutingEngine()
    
    reference_path = "path/to/data/matsim"
    # Tính toán tác động nhưng không lưu vào database
    preview_results = routing_services.calculate_impact_of_route_change(route_id, new_stops, routing_engine, uow, reference_path)
    return preview_results # Trả JSON cho Frontend vẽ lại Preview

def api_confirm_change_route(route_id: str, new_stops: list[str]):
    """
    Entrypoint: Xác nhận lưu thay đổi tuyến.
    """
    uow = DummyUnitOfWork(AbstractRepository())
    
    reference_path = "path/to/data/matsim"
    # Gọi service lưu xuống Database
    routing_services.change_route_shape(route_id, new_stops, uow, reference_path)
    return {"status": "success"}

