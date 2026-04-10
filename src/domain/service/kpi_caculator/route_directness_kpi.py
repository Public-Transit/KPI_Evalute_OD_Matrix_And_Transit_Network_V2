from typing import Any
from src.domain.service.kpi_caculator.kpi_base import KPICalculator
from src.domain.model.routing_result import EvaluatedRoutingOption
from src.domain.model.transit_network import TransitNetwork
from src.domain.service.spatial import find_cricuity_index_of_a_trip
from src.domain.port import IGeometryCalculator
from src.domain.model.trip import Trip

class RouteDirectnessCalculator(KPICalculator):
    def calculate(self, evaluated_routing_option: EvaluatedRoutingOption, **kwargs) -> dict[str, Any]:
        """
        Tính toán KPI độ trực tiếp của tuyến (Route Directness).
        Là giá trị nghịch đảo của độ vòng vèo (Circuity Index).

        
        Required kwargs:
            transit_network (TransitNetwork): Mạng lưới xe buýt
            geometry_calculator (IGeometryCalculator): Công cụ tính toán không gian
        """
        transit_network: TransitNetwork = kwargs.get("transit_network")
        geometry_calculator: IGeometryCalculator = kwargs.get("geometry_calculator")
        if not transit_network or not geometry_calculator:
            raise ValueError("Cần cung cấp 'transit_network' và 'geometry_calculator' để tính Route Directness")
            
        representative_trip: Trip = evaluated_routing_option.representative_trip()
        
        if not representative_trip or not representative_trip.legs:
            return {
                "score": "Not valid",
                "route_sequence": [],
                "stop_sequence": []
            }
            
        # Trạm đầu và trạm cuối của hành trình
        start_stop_id = representative_trip.legs[0].board_stop_id
        end_stop_id = representative_trip.legs[-1].alight_stop_id
        
        circuity_index = find_cricuity_index_of_a_trip(
            trip=representative_trip,
            start_stop_id=start_stop_id,
            end_stop_id=end_stop_id,
            transit_network=transit_network,
            geometry_calculator=geometry_calculator
        )
        
        score = 1.0 / circuity_index if circuity_index > 0 else float('inf')
        
        # Tạo danh sách tuyến và trạm để trả về
        route_sequence = [leg.route_id for leg in representative_trip.legs]
        stop_sequence = []
        for leg in representative_trip.legs:
            if not stop_sequence:
                stop_sequence.append(leg.board_stop_id)
            if leg.board_stop_id != stop_sequence[-1]:
                stop_sequence.append(leg.board_stop_id)
            stop_sequence.append(leg.alight_stop_id)
            
        return {
            "score": score,
            "route_sequence": route_sequence,
            "stop_sequence": stop_sequence
        }
