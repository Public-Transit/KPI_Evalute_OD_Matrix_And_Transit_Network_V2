# src/service_layer/service/routing_services.py
from src.service_layer.unit_of_work import AbstractUnitOfWork
from src.domain.service.routing import AbstractRouting
from src.domain.service.filter import AbstractCandidateTripFilter
from src.domain.model.routing_result import ODRoutingResult
from src.domain.model.route import Route
from src.domain.model.transit_network import TransitNetwork
from src.domain.port import IGeometryCalculator
from src.domain.model.od_matrix import ODMatrix

from src.domain.service.filter_v2 import AbstractCandidateTripFilterV2
from src.domain.model.routing_result_v2 import ODRoutingResultV2

def batch_route_all_od_pairs(routing_engine: AbstractRouting, filter_engine: AbstractCandidateTripFilter, uow: AbstractUnitOfWork, geo_calc: IGeometryCalculator, reference_path: str) -> list[ODRoutingResult]:
    """
    Application Service để đọc toàn bộ OD Matrix và định tuyến bằng Transit Network.
    """
    results = []
    
    with uow:
        # Lấy được toàn bộ Data từ Repo theo chuẩn get() tuple của AbstractRepository
        stops, routes, zones, od_pairs, trips = uow.repo.get(reference_path)
        
        # Ghép data thô thành Aggregates/Core Entities của Domain
        transit_network = TransitNetwork(stops, routes)
        od_matrix = ODMatrix(od_pairs, zones)
        
        # Giả sử od_pairs chứa danh sách ODPair object
        for od_pair in od_pairs:
            # Code domain định tuyến
            candidate_trips = routing_engine.find_candidate_trips_for_od_pair(od_pair, od_matrix, transit_network, geo_calc)
            
            # TODO: Dùng Filter để chọn trip tốt nhất
            best_trip = filter_engine.filter(od_pair, od_matrix, transit_network, candidate_trips, geo_calc)
            
            # Bọc kết quả
            results.append(ODRoutingResult(od_pair.id(), candidate_trips, best_trip))
            
    return results

def change_route_shape(route_id: str, new_stops: list[str], uow: AbstractUnitOfWork, geo_calc: IGeometryCalculator, reference_path: str):
    """
    Application Service đại diện khi người dùng chỉnh sửa 1 tuyến (thêm/bớt stop).
    """
    with uow:
        # Lấy network từ DB
        stops, routes, zones, od_pairs, trips = uow.repo.get(reference_path)
        
        route_to_update = next((r for r in routes if r.id() == route_id), None)
        
        if route_to_update:
            # Nếu đang thiết kế DDD, đối tượng Route sẽ có method cập nhật
            # route_to_update.update_stops(new_stops)
            pass
        
        # Lưu xuống DB qua UoW
        uow.commit()

def calculate_impact_of_route_change(route_id: str, new_stops: list[str], routing_engine: AbstractRouting, uow: AbstractUnitOfWork,  geo_calc: IGeometryCalculator, reference_path: str) -> list[ODRoutingResult]:
    """
    Service tạo 1 transit network clone/modify in-memory để tính lại điểm của cặp OD khi thay đổi tuyến (mà chưa cần lưu vào DB).
    """
    results = []
    with uow:
        stops, routes, zones, od_pairs, trips = uow.repo.get(reference_path)
        transit_network = TransitNetwork(stops, routes)
        od_matrix = ODMatrix(od_pairs, zones)
        
        # Sửa in-memory trên entity
        route_to_update = next((r for r in transit_network.get_routes() if r.id() == route_id), None)
        if route_to_update:
            # route_to_update.update_stops(new_stops)
            pass
        
        # Định tuyến lại với mạng lưới mới để xem tác động
        for od_pair in od_pairs:
            candidate_trips = routing_engine.find_candidate_trips_for_od_pair(od_pair, od_matrix, transit_network, geo_calc)
            results.append(ODRoutingResult(od_pair.id(), candidate_trips, None))
            
    # Lưu ý: Không gọi uow.commit() để không lưu sự thay đổi này xuống DB!
    return results

def batch_route_all_od_pairs_v2(routing_engine: AbstractRouting, filter_engine_v2: AbstractCandidateTripFilterV2, uow: AbstractUnitOfWork, geo_calc: IGeometryCalculator, reference_path: str) -> list[ODRoutingResultV2]:
    """
    Application Service V2: Áp dụng Filter V2 cho từng CandidateTrip. Trả về tất cả các Present Trips.
    """
    results = []
    
    with uow:
        # Lấy data từ Repo
        stops, routes, zones, od_pairs, trips = uow.repo.get(reference_path)
        transit_network = TransitNetwork(stops, routes)
        od_matrix = ODMatrix(od_pairs, zones)
        
        for od_pair in od_pairs:
            candidate_trips = routing_engine.find_candidate_trips_for_od_pair(od_pair, od_matrix, transit_network, geo_calc)
            
            present_trips = []
            for ct in candidate_trips:
                trip = filter_engine_v2.filter(od_pair, od_matrix, transit_network, ct, geo_calc)
                if trip:
                    present_trips.append(trip)
            
            results.append(ODRoutingResultV2(od_pair.id(), candidate_trips, present_trips))
            
    return results
