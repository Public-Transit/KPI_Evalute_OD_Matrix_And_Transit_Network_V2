from abc import ABC, abstractmethod

from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.trip import CandidateTrip
from src.domain.model.leg import CandidateLeg
from src.domain.service.spatial import find_all_routes_pass_through_zone, find_all_stops_on_a_route_located_in_a_certain_zone
from src.domain.port import IGeometryCalculator

class AbstractRouting(ABC):
    @abstractmethod
    def find_candidate_trips_for_od_pair(self, od_pair: ODPair, od_matrix: ODMatrix, transit_network: TransitNetwork, geometry_calculator: IGeometryCalculator) -> list[CandidateTrip]:
        pass

class DirectConnectionRouting(AbstractRouting):
    def find_candidate_trips_for_od_pair(self, od_pair: ODPair, od_matrix: ODMatrix, transit_network: TransitNetwork, geometry_calculator: IGeometryCalculator) -> list[CandidateTrip]:
        origin_zone = od_matrix.get_zone_by_id(od_pair.origin_zone_id())
        dest_zone = od_matrix.get_zone_by_id(od_pair.destination_zone_id())
        
        origin_routes = find_all_routes_pass_through_zone(origin_zone, transit_network, geometry_calculator)
        dest_routes = find_all_routes_pass_through_zone(dest_zone, transit_network, geometry_calculator)
        
        # Tuyến chung đi qua cả 2 vùng
        common_routes = [r for r in origin_routes if r in dest_routes]
        
        candidate_trips = []
        for route in common_routes:
            origin_stops = find_all_stops_on_a_route_located_in_a_certain_zone(origin_zone, route, transit_network, geometry_calculator)
            dest_stops = find_all_stops_on_a_route_located_in_a_certain_zone(dest_zone, route, transit_network, geometry_calculator)
            
            valid_origin_stops = set()
            valid_dest_stops = set()
            
            # Áp dụng điều kiện thứ tự: Trạm lên phải nằm TRƯỚC trạm xuống
            stops_seq = route.stops_seq()
            for o_stop in origin_stops:
                for d_stop in dest_stops:
                    if stops_seq.index(o_stop.id()) < stops_seq.index(d_stop.id()):
                        valid_origin_stops.add(o_stop.id())
                        valid_dest_stops.add(d_stop.id())
            
            if valid_origin_stops and valid_dest_stops:
                leg = CandidateLeg(route.id(), valid_origin_stops, valid_dest_stops)
                candidate_trips.append(CandidateTrip([leg]))
                
        return candidate_trips

class OneTransferRoutingEngine(AbstractRouting):
    def find_candidate_trips_for_od_pair(self, od_pair: ODPair, od_matrix: ODMatrix, transit_network: TransitNetwork, geometry_calculator: IGeometryCalculator) -> list[CandidateTrip]:
        origin_zone = od_matrix.get_zone_by_id(od_pair.origin_zone_id())
        dest_zone = od_matrix.get_zone_by_id(od_pair.destination_zone_id())
        
        origin_routes = find_all_routes_pass_through_zone(origin_zone, transit_network, geometry_calculator)
        dest_routes = find_all_routes_pass_through_zone(dest_zone, transit_network, geometry_calculator)
        
        # Loại bỏ các tuyến có thể đi thẳng
        common_routes_set = {r.id() for r in origin_routes if r in dest_routes}
        r1_list = [r for r in origin_routes if r.id() not in common_routes_set]
        r2_list = [r for r in dest_routes if r.id() not in common_routes_set]
        
        candidate_trips = []
        for r1 in r1_list:
            for r2 in r2_list:
                # Tìm trạm chung làm trung chuyển bằng phép giao của Python built-in set
                shared_stop_ids = set(r1.stops_seq()).intersection(set(r2.stops_seq()))
                if not shared_stop_ids:
                    continue
                
                origin_stops = find_all_stops_on_a_route_located_in_a_certain_zone(origin_zone, r1, transit_network, geometry_calculator)
                dest_stops = find_all_stops_on_a_route_located_in_a_certain_zone(dest_zone, r2, transit_network, geometry_calculator)
                
                r1_seq = r1.stops_seq()
                r2_seq = r2.stops_seq()
                
                valid_origin_stops = set()
                valid_transfer_stops = set()
                valid_dest_stops = set()
                
                for s_stop_id in shared_stop_ids:
                    s_idx1 = r1_seq.index(s_stop_id)
                    s_idx2 = r2_seq.index(s_stop_id)
                    
                    # Tuyến 1: Trạm lên TRƯỚC KHI tới Trạm trung chuyển
                    o_stops = [o for o in origin_stops if r1_seq.index(o.id()) < s_idx1]
                    # Tuyến 2: Trạm trung chuyển TRƯỚC KHI tới Trạm xuống
                    d_stops = [d for d in dest_stops if s_idx2 < r2_seq.index(d.id())]
                    
                    if o_stops and d_stops:
                        valid_transfer_stops.add(s_stop_id)
                        valid_origin_stops.update([o.id() for o in o_stops])
                        valid_dest_stops.update([d.id() for d in d_stops])
                        
                if valid_transfer_stops:
                    leg1 = CandidateLeg(r1.id(), valid_origin_stops, valid_transfer_stops)
                    leg2 = CandidateLeg(r2.id(), valid_transfer_stops, valid_dest_stops)
                    candidate_trips.append(CandidateTrip([leg1, leg2]))
                    
        return candidate_trips

class CombinedRoutingEngine(AbstractRouting):
    def __init__(self):
        self.direct = DirectConnectionRouting()
        self.one_transfer = OneTransferRoutingEngine()
        
    def find_candidate_trips_for_od_pair(self, od_pair: ODPair, od_matrix: ODMatrix, transit_network: TransitNetwork, geometry_calculator: IGeometryCalculator) -> list[CandidateTrip]:
        trips = self.direct.find_candidate_trips_for_od_pair(od_pair, od_matrix, transit_network, geometry_calculator)
        trips.extend(self.one_transfer.find_candidate_trips_for_od_pair(od_pair, od_matrix, transit_network, geometry_calculator))
        return trips
