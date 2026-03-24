from abc import ABC, abstractmethod
from src.domain.model.trip import CandidateTrip, Trip
from src.domain.model.leg import Leg
from src.domain.model.od_pair import ODPair
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.domain.service.spatial import find_closest_stop_to_centroid
from src.domain.port import IGeometryCalculator

class AbstractRoutesFilter(ABC):
    @abstractmethod
    def filter(self, od_pair: ODPair, od_matrix: ODMatrix, transit_network: TransitNetwork, candidate_trip: CandidateTrip, geometry_calculator: IGeometryCalculator) -> Trip:
        pass

class FilterStrategy(AbstractRoutesFilter):
    def filter(self, od_pair: ODPair, od_matrix: ODMatrix, transit_network: TransitNetwork, candidate_trip: CandidateTrip, geometry_calculator: IGeometryCalculator) -> Trip:
        if not candidate_trip:
            return None
            
        origin_zone = od_matrix.get_zone_by_id(od_pair.origin_zone_id())
        dest_zone = od_matrix.get_zone_by_id(od_pair.destination_zone_id())
        
        origin_centroid = origin_zone.centroid() if hasattr(origin_zone, 'centroid') else origin_zone.coord() if hasattr(origin_zone, 'coord') else None
        dest_centroid = dest_zone.centroid() if hasattr(dest_zone, 'centroid') else dest_zone.coord() if hasattr(dest_zone, 'coord') else None
        
        if not origin_centroid or not dest_centroid:
            return None 

        resolved_legs = []
        is_0_transfer = len(candidate_trip.candidate_legs) == 1
        
        if is_0_transfer:
            leg = candidate_trip.candidate_legs[0]
            board_stop = find_closest_stop_to_centroid(origin_zone, transit_network, geometry_calculator)
            alight_stop = find_closest_stop_to_centroid(dest_zone, transit_network, geometry_calculator)
            resolved_legs.append(Leg(leg.route_id, board_stop.id(), alight_stop.id()))
            
        else:
            leg1 = candidate_trip.candidate_legs[0]
            leg2 = candidate_trip.candidate_legs[1]
            
            board_stop = find_closest_stop_to_centroid(origin_zone, transit_network, geometry_calculator)
            alight_stop = find_closest_stop_to_centroid(dest_zone, transit_network, geometry_calculator)
            min_transfer_dist = float('inf')
            
            for t_id in leg1.possible_alighting_stop_ids:
                stop = transit_network.get_stop_by_id(t_id)
                if not stop: continue
                
                dist_o = stop.coord().distance_to(board_stop.coord(), geometry_calculator)
                dist_d = stop.coord().distance_to(alight_stop.coord(), geometry_calculator)
                total_dist = dist_o + dist_d
                
                if total_dist < min_transfer_dist:
                    min_transfer_dist = total_dist
                    best_transfer_stop = stop
                    
            resolved_legs.append(Leg(leg1.route_id, board_stop.id(), best_transfer_stop.id()))
            resolved_legs.append(Leg(leg2.route_id, best_transfer_stop.id(), alight_stop.id()))
            
        return Trip(resolved_legs)
