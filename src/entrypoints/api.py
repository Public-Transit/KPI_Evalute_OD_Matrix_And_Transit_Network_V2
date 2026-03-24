# src/entrypoints/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.service_layer.unit_of_work import DummyUnitOfWork
from src.adapters.repository.fake_reapository import FakeRepository
from src.domain.service.routing import CombinedRoutingEngine
from src.service_layer.service import routing_services
from src.domain.service.filter import MinDistanceCandidateTripFilter
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.od_matrix import ODMatrix

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
    repo = FakeRepository()
    uow = DummyUnitOfWork(repo)
    routing_engine = CombinedRoutingEngine()
    filter_engine = MinDistanceCandidateTripFilter()
    geo_calc = ShapelyGeometryCalculator()
    
    # 2. Chuyển giao logic cho Application Service
    try:
        results = routing_services.batch_route_all_od_pairs(routing_engine, filter_engine, uow, geo_calc, DEFAULT_REFERENCE_PATH)
        # Chuyển đổi kết quả thành dict/json với chi tiết
        json_results = []
        for r in results:
            trips_data = []
            if r.candidate_trip():
                for ct in r.candidate_trip():
                    legs_str = " -> Trung chuyển -> ".join([f"Tuyến {leg.route_id}" for leg in ct.candidate_legs])
                    trips_data.append(legs_str)
                    
            best_trip_data = None
            if r.present_trip():
                best_trip_data = " ==> ".join([f"[{leg.route_id}] từ {leg.board_stop_id} đến {leg.alight_stop_id}" for leg in r.present_trip().legs])
                
            json_results.append({
                "od_pair": r.od_pair_id(),
                "total_candidate_paths": len(r.candidate_trip()) if r.candidate_trip() else 0,
                "all_candidate_paths": trips_data,
                "best_selected_trip": best_trip_data
            })
            
        return {"status": "success", "data": json_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/routes/{route_id}/preview")
def preview_change_route(route_id: str, request: RouteUpdateRequest):
    """
    Xem trước tác động của việc thay đổi tuyến (chưa lưu vào DB).
    """
    repo = FakeRepository()
    uow = DummyUnitOfWork(repo)
    routing_engine = CombinedRoutingEngine()
    
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
    repo = FakeRepository()
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

@app.post("/api/kpi/full-v2/calculate-all")
def full_v2_calculate_kpi_all_od_pairs():
    """
    Tính toàn bộ các chỉ số KPI bằng KPI Calculator sau khi định tuyến.
    """
    repo = FakeRepository()
    uow = DummyUnitOfWork(repo)
    routing_engine = CombinedRoutingEngine()
    filter_engine = MinDistanceCandidateTripFilter()
    geo_calc = ShapelyGeometryCalculator()
    
    try:
        results = routing_services.batch_route_all_od_pairs(routing_engine, filter_engine, uow, geo_calc, DEFAULT_REFERENCE_PATH)
        
        # Khởi tạo dữ liệu domain cho KPI Calculators
        stops, routes, zones, od_pairs, trips = uow.repo.get(DEFAULT_REFERENCE_PATH)
        transit_network = TransitNetwork(stops, routes)
        od_matrix = ODMatrix(od_pairs, zones)
        
        from src.domain.service.kpi_caculator import TransferRateCalculator, CircuityIndexCalculator, SpatialCoverageCalculator
        transfer_calc = TransferRateCalculator()
        circuity_calc = CircuityIndexCalculator()
        spatial_calc = SpatialCoverageCalculator()
        
        json_results = []
        for r in results:
            t_res = transfer_calc.calculate(r)
            c_res = circuity_calc.calculate(r, transit_network=transit_network, geometry_calculator=geo_calc)
            s_res = spatial_calc.calculate(r, od_matrix=od_matrix, transit_network=transit_network, geometry_calculator=geo_calc, radius_m=500.0)
            
            best_trip_data = None
            if r.present_trip():
                best_trip_data = " ==> ".join([f"[{leg.route_id}] từ {leg.board_stop_id} đến {leg.alight_stop_id}" for leg in r.present_trip().legs])
            
            json_results.append({
                "od_pair": r.od_pair_id(),
                "best_selected_trip": best_trip_data,
                "kpis": {
                    "transfer_kpi": t_res,
                    "circuity_kpi": c_res,
                    "spatial_coverage_kpi": s_res
                }
            })
            
        return {"status": "success", "data": json_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
