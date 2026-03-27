# src/entrypoints/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.service_layer.unit_of_work import DummyUnitOfWork
from src.adapters.repository.fake_reapository import FakeRepository
from src.adapters.repository.visualize_zone_and_transitnetwork import VisualizeZoneAndTransitNetwork
from src.domain.service.routing import CombinedRoutingEngine
from src.service_layer.service import routing_services

from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.od_matrix import ODMatrix
from src.domain.service.kpi_caculator import TransferRateCalculator, CircuityIndexCalculator
from src.domain.service.filter_v2 import MinDistanceCandidateTripFilterV2


from src.adapters.repository.fake_repo_l1 import FakeRepoL1
from src.adapters.repository.fake_repo_l2 import FakeRepoL2
from src.adapters.repository.fake_repo_l3 import FakeRepoL3
from src.adapters.repository.fake_repo_l4 import FakeRepoL4
from src.adapters.repository.fake_repo_l5 import FakeRepoL5
from src.adapters.repository.fake_repo_f1 import FakeRepoF1
from src.adapters.repository.fake_repo_f2 import FakeRepoF2
from src.adapters.repository.fake_repo_f3 import FakeRepoF3
from src.adapters.repository.fake_repo_f4 import FakeRepoF4
from src.adapters.repository.fake_repo_f5 import FakeRepoF5


app = FastAPI(title="Transit Network KPI API", description="API định tuyến và đánh giá KPI mạng lưới giao thông")

# --- Các class Request Body (Data Transfer Objects) ---
class RouteUpdateRequest(BaseModel):
    new_stops: list[str]

# Tham chiếu mặc định tới file config/database
DEFAULT_REFERENCE_PATH = "path/to/data/matsim"




@app.post("/api/kpi/calculate-all")
def calculate_kpi_all_od_pairs():
    """
    Tính toàn bộ các chỉ số KPI bằng KPI Calculator sau khi tìm đường qua GenerateODRoutingResultService.
    """
    repo = FakeRepoL4()
    uow = DummyUnitOfWork(repo)
    routing_engine = CombinedRoutingEngine()
    filter_engine = MinDistanceCandidateTripFilterV2()
    geo_calc = ShapelyGeometryCalculator()
    
    try:
        results = routing_services.batch_route_all_od_pairs(routing_engine, filter_engine, uow, geo_calc, DEFAULT_REFERENCE_PATH)
        
        stops, routes, zones, od_pairs, trips = uow.repo.get(DEFAULT_REFERENCE_PATH)
        transit_network = TransitNetwork(stops, routes)
        od_matrix = ODMatrix(od_pairs, zones)
        
        transfer_calc = TransferRateCalculator()
        circuity_calc = CircuityIndexCalculator()
        
        json_results = []
        for r in results:
            opts_data = []
            for opt in r.evaluated_routing_options():
                t_res = transfer_calc.calculate(opt)
                c_res = circuity_calc.calculate(opt, transit_network=transit_network, geometry_calculator=geo_calc)
                
                # Trích xuất dữ liệu của opt một cách tối ưu
                candidate_routes = [leg.route_id for leg in opt.candidate_trip().candidate_legs]
                
                rep_trip = opt.representative_trip()
                if rep_trip and rep_trip.legs:
                    rep_routes = [leg.route_id for leg in rep_trip.legs]
                    rep_stops = [leg.board_stop_id for leg in rep_trip.legs] + [rep_trip.legs[-1].alight_stop_id]
                else:
                    rep_routes = []
                    rep_stops = []
                    
                opts_data.append({
                    "candidate_routes": candidate_routes,
                    "representative_trip": {
                        "routes": rep_routes,
                        "stops": rep_stops
                    },
                    "kpis": {
                        "transfer_kpi": t_res,
                        "circuity_kpi": c_res
                    }
                })
            
            json_results.append({
                "od_pair": r.od_pair_id(),
                "options": opts_data
            })
            
        return {"status": "success", "data": json_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
