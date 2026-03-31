from src.domain.model.zone import Zone
from src.domain.model.route import Route
from src.domain.model.stop import Stop
from src.domain.model.od_pair import ODPair
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.trip import Trip
from src.domain.port import IGeometryCalculator

def find_all_routes_pass_through_zone(zone: Zone, transit_network: TransitNetwork, geometry_calculator: IGeometryCalculator) -> list[Route]:
    """
    Lọc ra danh sách các tuyến đường có đi qua một Zone cụ thể.
    """
    passing_routes = []
        
    for route in transit_network.routes():
        for stop_id in route.stops_seq():
            stop = transit_network.get_stop_by_id(stop_id)
            if stop and zone.is_point_in_zone(stop.coord(), geometry_calculator):
                passing_routes.append(route)
                break
                   
    return passing_routes            

def find_all_stops_on_a_route_located_in_a_certain_zone(zone: Zone, route: Route, transit_network: TransitNetwork, geometry_calculator: IGeometryCalculator) -> list[Stop]:
    """
    Tìm ra các trạm dừng của 1 tuyến nằm trong 1 vùng cho trước.
    """
    passing_stops = []
    for stop_id in route.stops_seq():
        stop = transit_network.get_stop_by_id(stop_id)
        if stop and zone.is_point_in_zone(stop.coord(), geometry_calculator):
            passing_stops.append(stop)
                
    return passing_stops

def find_cricuity_index_of_a_trip(trip: Trip, start_stop_id: str, end_stop_id: str, transit_network: TransitNetwork, geometry_calculator: IGeometryCalculator) -> float:
    """
    Tính độ vòng vèo (Circuity Index) của một hành trình chi tiết (Trip).
    Bằng tổng khoảng cách thực tế đi dọc THEO TUYẾN BUS chia cho 
    khoảng cách ĐƯỜNG THẲNG TRỰC TIẾP nối điểm Đầu-Cuối.
    """
    total_route_dist = 0.0
    for leg in trip.legs: 
        route = transit_network.get_route_by_id(leg.route_id)
        if route:
            start_stop = transit_network.get_stop_by_id(leg.board_stop_id)
            end_stop = transit_network.get_stop_by_id(leg.alight_stop_id)
            if start_stop and end_stop:
                total_route_dist += route.get_distance_between_two_stops(start_stop, end_stop, geometry_calculator)
            
    # Tính khoảng cách đường thẳng
    start_stop = transit_network.get_stop_by_id(start_stop_id)
    end_stop = transit_network.get_stop_by_id(end_stop_id)
    total_straight_dist = 0.0

    if start_stop and end_stop:
        total_straight_dist = start_stop.coord().distance_to(end_stop.coord(), geometry_calculator)
    if total_straight_dist == 0:
        return 1.0
        
    return total_route_dist / total_straight_dist

def find_closest_stop_to_centroid(zone: Zone, transit_network: TransitNetwork, geometry_calculator: IGeometryCalculator) -> Stop:
    """
    Tìm trạm dừng gần nhất so với trọng tâm của một Zone.
    """
    best_stop = None
    min_dist = float('inf')

    zone_centroid_coord = zone.centroid()
    stops = transit_network.stops()

    for stop in stops:
        if not stop: continue
        
        # Sử dụng trực tiếp hàm distance_to của Point class
        dist = stop.coord().distance_to(zone_centroid_coord, geometry_calculator)
        if dist < min_dist:
            min_dist = dist
            best_stop = stop
    return best_stop


def is_odpair_served_by_segment_of_route(od_pair_id: str, route_id : str, start_stop_id: str, end_stop_id: str, od_matrix: ODMatrix, transit_network: TransitNetwork, geometry_calculator: IGeometryCalculator) -> bool:
    """
    Kiểm tra xem một cặp OD có được phục vụ bởi một đoạn của tuyến đường hay không.
    Logic (dựa theo quy trình 3 bước):
    1. Tìm tất cả các trạm của tuyến nằm trong Origin Zone (o_indices) và Destination Zone (d_indices).
    2. Xác định các khoảng đi hợp lệ [o_idx, d_idx] (điều kiện o_idx < d_idx).
    3. Xét xem quãng đường di chuyển của khách có mượn qua đoạn Segment [start_stop, end_stop] hay không bằng điều kiện overlap.
    """
    od_pair = od_matrix.get_od_pair_by_id(od_pair_id)
    if not od_pair: return False

    origin_zone = od_matrix.get_zone_by_id(od_pair.origin_zone_id())
    dest_zone = od_matrix.get_zone_by_id(od_pair.destination_zone_id())
    route = transit_network.get_route_by_id(route_id)

    if not route or not origin_zone or not dest_zone:
        return False

    stops_seq = route.stops_seq()
    try:
        s1_idx = stops_seq.index(start_stop_id)
        s2_idx = stops_seq.index(end_stop_id)
    except ValueError:
        return False

    # Đảm bảo S1 <= S2 theo đúng chiều
    if s1_idx > s2_idx:
        s1_idx, s2_idx = s2_idx, s1_idx

    # Bước 1: Tìm xem tuyến có phục vụ O, D không
    o_indices = []
    d_indices = []
    for i, stop_id in enumerate(stops_seq):
        stop = transit_network.get_stop_by_id(stop_id)
        if not stop: continue
        
        if origin_zone.is_point_in_zone(stop.coord(), geometry_calculator):
            o_indices.append(i)
        if dest_zone.is_point_in_zone(stop.coord(), geometry_calculator):
            d_indices.append(i)

    if not o_indices or not d_indices:
        return False

    # Bước 2 & 3: Tìm khoảng hợp lệ [o, d] và kiểm tra đoạn Segment có giao cắt không
    for o_idx in o_indices:
        for d_idx in d_indices:
            if o_idx < d_idx: # Chiều đi hợp lệ trên tuyếhách đi từ o_idx n
                # Kiểm tra chồng lấn: Kđến d_idx có đi chung đoạn đường S1_idx đến S2_idx?
                if max(o_idx, s1_idx) <= min(d_idx, s2_idx):
                    return True # Chỉ cần có ít nhất 1 cách di chuyển hợp lệ

    return False
    
def get_served_od_pairs_from_segment(route_id: str, start_stop_id: str, end_stop_id: str,
                                         od_matrix: ODMatrix, transit_network: TransitNetwork, 
                                         geometry_calculator: IGeometryCalculator) -> set[ODPair]:
        served_od_pairs = set()
        for od_pair in od_matrix.od_pairs():
            if is_odpair_served_by_segment_of_route(od_pair.id(), route_id, start_stop_id, end_stop_id, od_matrix, transit_network, geometry_calculator):
                served_od_pairs.add(od_pair)
        return served_od_pairs
   
    
        
