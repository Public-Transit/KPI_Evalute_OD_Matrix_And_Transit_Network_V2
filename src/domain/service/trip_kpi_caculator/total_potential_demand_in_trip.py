from typing import Any
from src.domain.model.trip import Trip
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.port import IGeometryCalculator
from src.domain.service.routing import AbstractRouting
from src.domain.model.trip import CandidateTrip, Leg
from src.domain.service.trip_kpi_caculator.trip_kpi_base import TripKPICalculator


def find_trip_served_od_pair_in_transit_network_makeby_routes_in_trip(
    od_pair: ODPair, 
    trip: Trip, 
    od_matrix: ODMatrix, 
    transit_network: TransitNetwork, 
    routing_engine: AbstractRouting, 
    geometry_calculator: IGeometryCalculator
) -> list[Trip]:
    """
    Kiểm tra xem một cặp OD có được phục vụ bởi một hành trình chi tiết (Trip) hay không.
    Nếu có được phụ vụ trả ra 1 trip con trip_subset của trip_input vào thể hiện rằng: Nêu mạng lưới chỉ có các route trong trip_input, thì trip_od kết nối OD đầu vào thì trip _od đó sẽ đi quan đoạn trip_subset của trip_input
    Logic (dựa theo quy trình 3 bước):
    Bước 1: Tìm cách di chuyển hợp lệ candidate_trip_od từ O đến D dựa trên các route có trong trip
    Bước 2: Xét từng leg trong candidate_trip_od, nếu nó có giao với 1 trong các leg trong trip_input thì trả ra đoạn giao theo dạng leg_giao_i
    Bước 3: Trả ra các trip_subset là giao của candidate_trip_od và trip_input
    """
    # --- Bước 1: Tạo ra 1 transit network chỉ chứa các route có trong trip ---
    route_ids_in_trip = set()
    routes_objs = []
    for leg in trip.legs:
        route = transit_network.get_route_by_id(leg.route_id)
        if route and route.id() not in route_ids_in_trip:
            route_ids_in_trip.add(route.id())
            routes_objs.append(route)

    #sub_transitnetwork = TransitNetwork(transit_network.stops(), routes_objs)
    sub_transitnetwork = transit_network
    # --- Bước 2: Tìm cách di chuyển hợp lệ candidate_trips_od từ O đến D trên các route có trong trip ---
    candidate_trips_od = routing_engine.find_candidate_trips_for_od_pair(
        od_pair, od_matrix, sub_transitnetwork, geometry_calculator
    )
    if not candidate_trips_od:
        return []

    # --- Bước 3: Xét sự giao nhau để sinh ra các phần nhỏ (partial overlaps) ---
    served_trip_subsets = []
    
    for candidate_trip in candidate_trips_od:
        overlapped_legs = []
        for c_leg in candidate_trip.candidate_legs:
            for t_leg in trip.legs:
                if c_leg.route_id == t_leg.route_id:
                    route = transit_network.get_route_by_id(t_leg.route_id)
                    if not route: continue
                    seq = route.stops_seq()
                    
                    try:
                        t_start = seq.index(t_leg.board_stop_id)
                        t_end = seq.index(t_leg.alight_stop_id)
                    except ValueError:
                        continue
                        
                    if t_start > t_end: t_start, t_end = t_end, t_start
                    
                    c_boards = [seq.index(s) for s in c_leg.possible_boarding_stop_ids if s in seq]
                    c_alights = [seq.index(s) for s in c_leg.possible_alighting_stop_ids if s in seq]
                    if not c_boards or not c_alights: 
                        continue
                        
                    c_start = min(c_boards)
                    c_end = max(c_alights)
                    
                    i_start = max(t_start, c_start)
                    i_end = min(t_end, c_end)
                    
                    if i_start <= i_end:
                        overlapped_legs.append(Leg(route.id(), seq[i_start], seq[i_end]))
                        
        if overlapped_legs:
            served_trip_subsets.append(Trip(legs=overlapped_legs))

    return served_trip_subsets


class TotalPotentialDemandInTripCalculator(TripKPICalculator):
    def calculate(
        self, 
        trip: Trip, 
        transit_network: TransitNetwork, 
        od_matrix: ODMatrix, 
        routing_engine: AbstractRouting,
        geometry_calculator: IGeometryCalculator
    ) -> dict[str, Any]:
        """
        Tính toán KPI về tổng nhu cầu tiềm năng được thỏa mãn bởi 1 cách đi (Trip).
        Trả về: {
            "total_demand": float,
            "served_od_details": [
                {"od_pair_id": str, "demand": float, "board_stop": str, "alight_stop": str}, ...
            ]
        }
        """
        total_potential_demand = 0.0
        served_od_details = []

        for od_pair in od_matrix.od_pairs():
            served_subsets = find_trip_served_od_pair_in_transit_network_makeby_routes_in_trip(
                od_pair, trip, od_matrix, transit_network, routing_engine, geometry_calculator
            )
            
            if served_subsets:
                demand = od_pair.demand()
                total_potential_demand += demand
                
                # Lấy thông tin trạm đầu và trạm cuối của trip subset phục vụ OD này
                # Giả định lấy subset đầu tiên nếu có nhiều (thường chỉ có 1 do route subset)
                first_subset = served_subsets[0]
                served_od_details.append({
                    "od_pair_id": od_pair.id(),
                    "demand": float(demand),
                    "board_stop": first_subset.legs[0].board_stop_id,
                    "alight_stop": first_subset.legs[-1].alight_stop_id
                })

        return {
            "total_demand": float(total_potential_demand),
            "served_od_details": served_od_details
        }
