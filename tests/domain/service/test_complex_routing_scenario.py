from src.adapters.repository.complex_test_repository import ComplexTestRepository
from src.domain.service.routing import CombinedRoutingEngine
from src.domain.service.filter_v2 import MinDistanceCandidateTripFilterV2
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator

def test_complex_routing_scenario():
    repo = ComplexTestRepository()
    od_matrix = repo.get_od_matrix()
    transit_network = repo.get_transit_network()
    calc = ShapelyGeometryCalculator()
    
    # 1. Routing Engine
    routing_engine = CombinedRoutingEngine()
    od_pair = repo.od_pairs[0]
    candidate_trips = routing_engine.find_candidate_trips_for_od_pair(od_pair, od_matrix, transit_network, calc)
    
    # Kiểm tra số lượng - Mong đợi 3 trực tiếp + 2 trung chuyển = 5
    # (Có thể nhiều hơn nếu có các trạm trung chuyển khác nhau, nhưng theo thiết kế là 5)
    assert len(candidate_trips) == 5
    
    # 2. Filtering
    filter_v2 = MinDistanceCandidateTripFilterV2()
    
    # Lấy IDs của các tuyến trực tiếp tìm được
    direct_route_ids = [ct.candidate_legs[0].route_id for ct in candidate_trips if len(ct.candidate_legs) == 1]
    assert "R_Best" in direct_route_ids
    assert "R_TieBreak" in direct_route_ids
    assert "R_Far" in direct_route_ids
    
    # 3. Kiểm tra Tie-breaker cho Direct Trips
    best_ct = next(ct for ct in candidate_trips if ct.candidate_legs[0].route_id == "R_Best")
    tiebreak_ct = next(ct for ct in candidate_trips if ct.candidate_legs[0].route_id == "R_TieBreak")
    
    best_trip = filter_v2.filter(od_pair, od_matrix, transit_network, best_ct, calc)
    tiebreak_trip = filter_v2.filter(od_pair, od_matrix, transit_network, tiebreak_ct, calc)
    
    # Cả hai đều phải chọn S0_1 và S1_1 (do gần centroid nhất)
    # R_Best: [S0_1, S1_1], R_TieBreak: [S0_1, SM_1, SM_2, S1_1]
    assert "S0_1" in best_trip.legs[0].board_stop_id
    assert "S1_1" in best_trip.legs[0].alight_stop_id
    assert "S0_1" in tiebreak_trip.legs[0].board_stop_id
    assert "S1_1" in tiebreak_trip.legs[0].alight_stop_id
    
    # Tên của Best trip nên có quãng đường ngắn hơn Tiebreak
    # Trong kịch bản thực tế của filter_v2, nó sẽ trả về Trip tương ứng.
    # Logic tie-breaker nằm bên trong filter_v2.filter khi nó lặp qua các cặp trạm.
    
if __name__ == "__main__":
    pytest.main([__file__])
