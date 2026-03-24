# src/entrypoints/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.service_layer.unit_of_work import DummyUnitOfWork
from src.adapters.repository.abstract_repository import AbstractRepository # Cần implement thực tế
from src.domain.service.routing import OneTransferRoutingEngine
from src.service_layer.service import routing_services
from src.domain.service.filter import FilterStrategy
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator

app = FastAPI(title="Transit Network KPI API", description="API định tuyến và đánh giá KPI mạng lưới giao thông")

# --- Các class Request Body (Data Transfer Objects) ---
class RouteUpdateRequest(BaseModel):
    new_stops: list[str]

# Tham chiếu mặc định tới file config/database
DEFAULT_REFERENCE_PATH = "path/to/data/matsim"

@app.post("/api/kpi/calculate-all")
def calculate_kpi_all_od_pairs():
    """
    Tính KPI cho toàn bộ ODPair trong hệ thống.
    """
    # 1. Khởi tạo cơ sở hạ tầng (Dependencies)
    repo = AbstractRepository()
    uow = DummyUnitOfWork(repo)
    routing_engine = OneTransferRoutingEngine()
    filter_engine = FilterStrategy()
    geo_calc = ShapelyGeometryCalculator()
    
    # 2. Chuyển giao logic cho Application Service
    try:
        results = routing_services.batch_route_all_od_pairs(routing_engine, filter_engine, uow, geo_calc, DEFAULT_REFERENCE_PATH)
        # Chuyển đổi kết quả thành dict/json
        json_results = [{"od_pair_id": r.od_pair_id(), "candidate_trips": len(r.candidate_trip().candidate_legs) if r.candidate_trip() else 0} for r in results]
        return {"status": "success", "data": json_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/routes/{route_id}/preview")
def preview_change_route(route_id: str, request: RouteUpdateRequest):
    """
    Xem trước tác động của việc thay đổi tuyến (chưa lưu vào DB).
    """
    repo = AbstractRepository()
    uow = DummyUnitOfWork(repo)
    routing_engine = OneTransferRoutingEngine()
    
    try:
        preview_results = routing_services.calculate_impact_of_route_change(
            route_id, 
            request.new_stops, 
            routing_engine, 
            uow, 
            DEFAULT_REFERENCE_PATH
        )
        return {"status": "success", "preview_data": "Thành công (giả lập)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/routes/{route_id}/confirm")
def confirm_change_route(route_id: str, request: RouteUpdateRequest):
    """
    Xác nhận và lưu thay đổi tuyến vào cơ sở dữ liệu.
    """
    repo = AbstractRepository()
    uow = DummyUnitOfWork(repo)
    
    try:
        routing_services.change_route_shape(
            route_id, 
            request.new_stops, 
            uow, 
            DEFAULT_REFERENCE_PATH
        )
        return {"status": "success", "message": f"Đã lưu thay đổi cho tuyến {route_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
