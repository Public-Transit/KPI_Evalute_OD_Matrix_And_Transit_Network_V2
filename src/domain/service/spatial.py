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
        
    for route in transit_network.get_routes():
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
    stops = transit_network.get_stops()

    for stop in stops:
        if not stop: continue
        
        # Sử dụng trực tiếp hàm distance_to của Point class
        dist = stop.coord().distance_to(zone_centroid_coord, geometry_calculator)
        if dist < min_dist:
            min_dist = dist
            best_stop = stop
    return best_stop

