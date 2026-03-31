from abc import ABC, abstractmethod
from src.domain.model.trip import CandidateTrip, Trip
from src.domain.model.leg import Leg
from src.domain.model.od_pair import ODPair
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.stop import Stop
from src.domain.model.point import Point
from src.domain.port import IGeometryCalculator


class AbstractCandidateTripFilterV2(ABC):
    @abstractmethod
    def filter(self, od_pair: ODPair, od_matrix: ODMatrix, transit_network: TransitNetwork, candidate_trip: CandidateTrip, geometry_calculator: IGeometryCalculator) -> Trip:
        pass

class AbstractTripsFilterV2(ABC):
    @abstractmethod
    def filter(self, od_pair: ODPair, od_matrix: ODMatrix, transit_network: TransitNetwork, trips: list[Trip], geometry_calculator: IGeometryCalculator) -> Trip:
        pass

class MinDistanceCandidateTripFilterV2(AbstractCandidateTripFilterV2):
    '''
    Lọc từ 1 candidate trip sang trip hoàn chỉnh.
    Các chặng boarding/alighting được chọn là trạm gần tâm zone nhất.
    Khoảng cách đi bộ được tối ưu. Đối với chuyến có trung chuyển, cũng tối ưu khoảng cách tuyến xe buýt.
    '''
    def filter(self, od_pair: ODPair, od_matrix: ODMatrix, transit_network: TransitNetwork, candidate_trip: CandidateTrip, geometry_calculator: IGeometryCalculator) -> Trip:
        if not candidate_trip or not candidate_trip.candidate_legs:
            return None
            
        origin_zone = od_matrix.get_zone_by_id(od_pair.origin_zone_id())
        dest_zone = od_matrix.get_zone_by_id(od_pair.destination_zone_id())
        
        origin_centroid = origin_zone.centroid()
        dest_centroid = dest_zone.centroid()
        
        if not origin_centroid or not dest_centroid:
            return None 

        if len(candidate_trip.candidate_legs) == 1:
            leg = candidate_trip.candidate_legs[0]
            route = transit_network.get_route_by_id(leg.route_id)
            
            best_pair = None
            min_access_score = float('inf')
            min_route_dist = float('inf')
            
            # Xét mọi cặp boarding/alighting có thể
            for b_id in leg.possible_boarding_stop_ids:
                b_stop = transit_network.get_stop_by_id(b_id)
                if not b_stop: continue
                
                for a_id in leg.possible_alighting_stop_ids:
                    a_stop = transit_network.get_stop_by_id(a_id)
                    if not a_stop: continue
                    
                    # 1. Tiêu chí chính: Khoảng cách đi bộ (túi tiền thời gian)
                    score = b_stop.coord().distance_to(origin_centroid, geometry_calculator) + \
                            a_stop.coord().distance_to(dest_centroid, geometry_calculator)
                    
                    # 2. Tiêu chí phụ: Quãng đường trên tuyến
                    route_dist = route.get_distance_between_two_stops(b_stop, a_stop, geometry_calculator)
                    
                    if score < min_access_score - 1e-4: # Tolerance 0.1mm
                        min_access_score = score
                        min_route_dist = route_dist
                        best_pair = (b_id, a_id)
                    elif abs(score - min_access_score) <= 1e-4:
                        if route_dist < min_route_dist:
                            min_route_dist = route_dist
                            best_pair = (b_id, a_id)
            
            if best_pair:
                return Trip([Leg(leg.route_id, best_pair[0], best_pair[1])])
                
        elif len(candidate_trip.candidate_legs) == 2:
            leg1 = candidate_trip.candidate_legs[0]
            leg2 = candidate_trip.candidate_legs[1]
            
            route1 = transit_network.get_route_by_id(leg1.route_id)
            route2 = transit_network.get_route_by_id(leg2.route_id)
            
            best_tuple = None
            min_access_score = float('inf')
            min_route_dist = float('inf')
            
            for b_id in leg1.possible_boarding_stop_ids:
                b_stop = transit_network.get_stop_by_id(b_id)
                if not b_stop: continue
                access_o = b_stop.coord().distance_to(origin_centroid, geometry_calculator)
                
                for a_id in leg2.possible_alighting_stop_ids:
                    a_stop = transit_network.get_stop_by_id(a_id)
                    if not a_stop: continue
                    access_d = a_stop.coord().distance_to(dest_centroid, geometry_calculator)
                    
                    score = access_o + access_d
                    
                    for t_id in leg1.possible_alighting_stop_ids: # transfer stops
                        t_stop = transit_network.get_stop_by_id(t_id)
                        if not t_stop: continue
                        
                        d1 = route1.get_distance_between_two_stops(b_stop, t_stop, geometry_calculator)
                        d2 = route2.get_distance_between_two_stops(t_stop, a_stop, geometry_calculator)
                        route_dist = d1 + d2
                        
                        if score < min_access_score - 1e-4:
                            min_access_score = score
                            min_route_dist = route_dist
                            best_tuple = (b_id, t_id, a_id)
                        elif abs(score - min_access_score) <= 1e-4:
                            if route_dist < min_route_dist:
                                min_route_dist = route_dist
                                best_tuple = (b_id, t_id, a_id)
            
            if best_tuple:
                return Trip([
                    Leg(leg1.route_id, best_tuple[0], best_tuple[1]),
                    Leg(leg2.route_id, best_tuple[1], best_tuple[2])
                ])
                
        return None

class GlobalMinDistanceTripsFilterV2:
    '''
    Lọc từ danh sách nhiều CandidateTrip -> Chốt 1 Trip duy nhất tối ưu nhất.
    '''
    def __init__(self):
        self.local_filter = MinDistanceCandidateTripFilterV2()

    def filter(self, od_pair: ODPair, od_matrix: ODMatrix, transit_network: TransitNetwork, candidate_trips: list[CandidateTrip], geometry_calculator: IGeometryCalculator) -> Trip:
        if not candidate_trips:
            return None
            
        best_trip = None
        min_access_score = float('inf')
        min_route_dist = float('inf')
        
        origin_zone = od_matrix.get_zone_by_id(od_pair.origin_zone_id())
        dest_zone = od_matrix.get_zone_by_id(od_pair.destination_zone_id())
        origin_centroid = origin_zone.centroid()
        dest_centroid = dest_zone.centroid()

        for candidate in candidate_trips:
            trip = self.local_filter.filter(od_pair, od_matrix, transit_network, candidate, geometry_calculator)
            if not trip:
                continue
                
            b_stop = transit_network.get_stop_by_id(trip.legs[0].board_stop_id)
            a_stop = transit_network.get_stop_by_id(trip.legs[-1].alight_stop_id)
            
            score = b_stop.coord().distance_to(origin_centroid, geometry_calculator) + \
                    a_stop.coord().distance_to(dest_centroid, geometry_calculator)
            
            route_dist = 0
            for leg in trip.legs:
                route = transit_network.get_route_by_id(leg.route_id)
                b = transit_network.get_stop_by_id(leg.board_stop_id)
                a = transit_network.get_stop_by_id(leg.alight_stop_id)
                route_dist += route.get_distance_between_two_stops(b, a, geometry_calculator)
            
            if score < min_access_score - 1e-4:
                min_access_score = score
                min_route_dist = route_dist
                best_trip = trip
            elif abs(score - min_access_score) <= 1e-4:
                if route_dist < min_route_dist - 1e-4:
                    min_route_dist = route_dist
                    best_trip = trip
        
        return best_trip


