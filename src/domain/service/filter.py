from abc import ABC, abstractmethod
from src.domain.model.trip import CandidateTrip, Trip
from src.domain.model.leg import Leg
from src.domain.model.od_pair import ODPair
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.stop import Stop
from src.domain.model.point import Point
from src.domain.port import IGeometryCalculator

class AbstractCandidateTripFilter(ABC):
    @abstractmethod
    def filter(self, od_pair: ODPair, od_matrix: ODMatrix, transit_network: TransitNetwork, candidate_trips: list[CandidateTrip], geometry_calculator: IGeometryCalculator) -> Trip:
        pass

def _get_closest_stop(stop_ids: set[str], centroid: Point, transit_network: TransitNetwork, calc: IGeometryCalculator) -> Stop:
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

class MinDistanceCandidateTripFilter(AbstractCandidateTripFilter):
    '''
    Chọn chặng ưu tiên: 
    1. Ưu tiên chọn các hành trình có số chặng nhỏ nhất
    2. Ưu tiên chọn các hành trình 1 chặng có tổng khoảng cách đi bộ nhỏ nhất từ tâm O đến tâm D
    3. Ưu tiên chọn các hành trình 2 chặng có tổng khoảng cách đi bộ nhỏ nhất từ tâm O đến tâm D và
       chọn trạm trung chuyển sao cho quãng đường tuyến là bé nhất theo hàm get_distance_between_two_stops.
    '''
    def filter(self, od_pair: ODPair, od_matrix: ODMatrix, transit_network: TransitNetwork, candidate_trips: list[CandidateTrip], geometry_calculator: IGeometryCalculator) -> Trip:
        if not candidate_trips:
            return None
            
        origin_zone = od_matrix.get_zone_by_id(od_pair.origin_zone_id())
        dest_zone = od_matrix.get_zone_by_id(od_pair.destination_zone_id())
        
        origin_centroid = origin_zone.centroid() if hasattr(origin_zone, 'centroid') else origin_zone.coord() if hasattr(origin_zone, 'coord') else None
        dest_centroid = dest_zone.centroid() if hasattr(dest_zone, 'centroid') else dest_zone.coord() if hasattr(dest_zone, 'coord') else None
        
        if not origin_centroid or not dest_centroid:
            return None 

        best_0_transfer_trip = None
        min_0_transfer_score = float('inf')
        
        best_1_transfer_trip = None
        min_1_transfer_score = float('inf')

        for ct in candidate_trips:
            # 1. Hành trình 1 chặng (0 transfer)
            if len(ct.candidate_legs) == 1:
                leg = ct.candidate_legs[0]
                board_stop = _get_closest_stop(leg.possible_boarding_stop_ids, origin_centroid, transit_network, geometry_calculator)
                alight_stop = _get_closest_stop(leg.possible_alighting_stop_ids, dest_centroid, transit_network, geometry_calculator)
                
                if board_stop and alight_stop:
                    score = board_stop.coord().distance_to(origin_centroid, geometry_calculator) + alight_stop.coord().distance_to(dest_centroid, geometry_calculator)
                    if score < min_0_transfer_score:
                        min_0_transfer_score = score
                        best_0_transfer_trip = Trip([Leg(leg.route_id, board_stop.id(), alight_stop.id())])
                        
            # 2. Hành trình 2 chặng (1 transfer)
            elif len(ct.candidate_legs) == 2:
                leg1 = ct.candidate_legs[0]
                leg2 = ct.candidate_legs[1]
                
                board_stop = _get_closest_stop(leg1.possible_boarding_stop_ids, origin_centroid, transit_network, geometry_calculator)
                alight_stop = _get_closest_stop(leg2.possible_alighting_stop_ids, dest_centroid, transit_network, geometry_calculator)
                
                if not board_stop or not alight_stop:
                    continue
                    
                transfer_stop_ids = leg1.possible_alighting_stop_ids
                best_transfer_stop_id = None
                
                if len(transfer_stop_ids) == 1:
                    best_transfer_stop_id = list(transfer_stop_ids)[0]
                elif len(transfer_stop_ids) > 1:
                    route1 = transit_network.get_route_by_id(leg1.route_id)
                    route2 = transit_network.get_route_by_id(leg2.route_id)
                    
                    min_route_dist = float('inf')
                    for t_id in transfer_stop_ids:
                        t_stop = transit_network.get_stop_by_id(t_id)
                        if not t_stop: continue
                        d1 = route1.get_distance_between_two_stops(board_stop, t_stop, geometry_calculator)
                        d2 = route2.get_distance_between_two_stops(t_stop, alight_stop, geometry_calculator)
                        if d1 + d2 < min_route_dist:
                            min_route_dist = d1 + d2
                            best_transfer_stop_id = t_id
                            
                if best_transfer_stop_id:
                    score = board_stop.coord().distance_to(origin_centroid, geometry_calculator) + alight_stop.coord().distance_to(dest_centroid, geometry_calculator)
                    if score < min_1_transfer_score:
                        min_1_transfer_score = score
                        best_1_transfer_trip = Trip([
                            Leg(leg1.route_id, board_stop.id(), best_transfer_stop_id),
                            Leg(leg2.route_id, best_transfer_stop_id, alight_stop.id())
                        ])
                        
        if best_0_transfer_trip:
            return best_0_transfer_trip
        if best_1_transfer_trip:
            return best_1_transfer_trip
            
        return None
