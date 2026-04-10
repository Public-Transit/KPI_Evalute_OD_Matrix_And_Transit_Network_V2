from src.domain.model.zone import Zone
from src.domain.model.route import Route
from src.domain.model.stop import Stop
from src.domain.model.od_pair import ODPair
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.trip import Trip, CandidateTrip
from src.domain.model.leg import Leg
from src.domain.port import IGeometryCalculator
from src.domain.model.point import Point

import itertools

def get_closest_stop(stop_ids: set[str], centroid: Point, transit_network: TransitNetwork, calc: IGeometryCalculator) -> Stop:
    best_stop = None
    min_dist = float('inf')
    for sid in stop_ids:
        stop = transit_network.get_stop_by_id(sid)
        if not stop: continue
        d = stop.coord().distance_to(centroid, calc)
        if d < min_dist:
            min_dist = d
            best_stop = stop
    return best_stop

def get_first_stop_in_route(stop_ids: set[str], route: Route) -> str:
    seq = route.stops_seq()
    first_stop_id = None
    min_idx = float('inf')
    for sid in stop_ids:
        try:
            idx = seq.index(sid)
            if idx < min_idx:
                min_idx = idx
                first_stop_id = sid
        except ValueError:
            pass
    return first_stop_id

def get_last_stop_in_route(stop_ids: set[str], route: Route) -> str:
    seq = route.stops_seq()
    last_stop_id = None
    max_idx = -1
    for sid in stop_ids:
        try:
            idx = seq.index(sid)
            if idx > max_idx:
                max_idx = idx
                last_stop_id = sid
        except ValueError:
            pass
    return last_stop_id

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

def find_intersecting_trip_between_candidatetrip_and_trip(candidate_trip: CandidateTrip, trip: Trip, transit_network: TransitNetwork) -> list[Trip]:
    """
    Tìm ra các trip giao giữa 1 candidate trip và 1 trip thực tế.
    Áp dụng logic giao cắt tập hợp (interval intersection) trên cùng một Route để xác định điểm biên (kể cả 1 Stop).
    """
    c_legs = candidate_trip.candidate_legs
    t_legs = trip.legs
    
    n_c = len(c_legs)
    n_t = len(t_legs)
    
    served_trip_subsets = []
    
    # Mappping index các leg của candidate_trip với trip_input
    for indices in itertools.combinations(range(n_t), n_c):
        # 1. Các route_id phải khớp nhau
        match_routes = True
        for i in range(n_c):
            if t_legs[indices[i]].route_id != c_legs[i].route_id:
                match_routes = False
                break
        if not match_routes:
            continue
            
        # Tính toán interval giao cho từng cặp (c_leg, t_leg)
        intersected_intervals = []
        valid_intersection = True
        
        for i in range(n_c):
            t_leg = t_legs[indices[i]]
            c_leg = c_legs[i]
            route = transit_network.get_route_by_id(t_leg.route_id)
            if not route:
                valid_intersection = False
                break
            
            seq = route.stops_seq()
            
            # Tọa độ interval của t_leg
            try:
                t_start = seq.index(t_leg.board_stop_id)
                t_end = seq.index(t_leg.alight_stop_id)
            except ValueError:
                valid_intersection = False
                break
                
            if t_start > t_end:
                t_start, t_end = t_end, t_start
                
            # Tọa độ interval của c_leg (phổ quát cover toàn bộ possible boards đến alights)
            c_boards = [seq.index(s) for s in c_leg.possible_boarding_stop_ids if s in seq]
            c_alights = [seq.index(s) for s in c_leg.possible_alighting_stop_ids if s in seq]
            
            if not c_boards or not c_alights:
                valid_intersection = False
                break
                
            c_start = min(c_boards)
            c_end = max(c_alights)
            
            # Phép giao của hai tập hợp (Interval Intersection)
            i_start = max(t_start, c_start)
            i_end = min(t_end, c_end)

            # Nếu không có đoạn giao nhau/ giao nhau ở 1 trạm thì bỏ qua
            if i_start > i_end:
                valid_intersection = False
                break
                
            intersected_intervals.append({
                'route_id': route.id(),
                'seq': seq,
                'start_idx': i_start,
                'end_idx': i_end
            })
            
        if not valid_intersection:
            continue
            
        # 2. Xây dựng Trip từ các đoạn giao
        if n_c == 1:
            interval = intersected_intervals[0]
            subset_trip = Trip(legs=[Leg(
                interval['route_id'], 
                interval['seq'][interval['start_idx']], 
                interval['seq'][interval['end_idx']]
            )])
            served_trip_subsets.append(subset_trip)
            
        elif n_c == 2:
            int1 = intersected_intervals[0]
            int2 = intersected_intervals[1]
            c_leg1 = c_legs[0]
            c_leg2 = c_legs[1]
            
            # Điểm chuyển tuyến phải thỏa mãn:
            # 1. Là giao của c_leg1.alights và c_leg2.boards
            # 2. Nằm trong cả hai interval giao của hai leg
            transfer_cands = set(c_leg1.possible_alighting_stop_ids).intersection(c_leg2.possible_boarding_stop_ids)
            
            for t_stop in transfer_cands:
                if t_stop not in int1['seq']: continue
                idx1 = int1['seq'].index(t_stop)
                if not (int1['start_idx'] <= idx1 <= int1['end_idx']): continue
                
                if t_stop not in int2['seq']: continue
                idx2 = int2['seq'].index(t_stop)
                if not (int2['start_idx'] <= idx2 <= int2['end_idx']): continue
                
                # Nối hai đoạn bằng trạm trung chuyển hợp lệ
                subset_trip = Trip(legs=[
                    Leg(int1['route_id'], int1['seq'][int1['start_idx']], t_stop),
                    Leg(int2['route_id'], t_stop, int2['seq'][int2['end_idx']])
                ])
                served_trip_subsets.append(subset_trip)
                break

    return served_trip_subsets

def reverse_route_to_trip(routes: list[Route]) -> list[Trip]:
    trips = []
    for route in routes:
        trips.append(Trip(legs=[Leg(route.id(), route.stops_seq()[0], route.stops_seq()[-1])]))
    return trips
        
