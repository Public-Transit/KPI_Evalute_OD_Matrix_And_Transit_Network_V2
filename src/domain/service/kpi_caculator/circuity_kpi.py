from typing import Any
from src.domain.service.kpi_caculator.kpi_base import KPICalculator
from src.domain.model.routing_result import ODRoutingResult
from src.domain.model.transit_network import TransitNetwork
from src.domain.service.spatial import find_cricuity_index_of_a_trip
from src.domain.port import IGeometryCalculator

class CircuityIndexCalculator(KPICalculator):
    def calculate(self, routing_result: ODRoutingResult, **kwargs) -> dict[str, Any]:
        """
        Tính toán KPI độ vòng vèo (Circuity Index)
        
        Required kwargs:
            transit_network (TransitNetwork): Mạng lưới xe buýt
            geometry_calculator (IGeometryCalculator): Công cụ tính toán không gian
        """
        transit_network: TransitNetwork = kwargs.get("transit_network")
        geometry_calculator: IGeometryCalculator = kwargs.get("geometry_calculator")
        if not transit_network or not geometry_calculator:
            raise ValueError("Cần cung cấp 'transit_network' và 'geometry_calculator' để tính Circuity Index")
            
        present_trip = routing_result.present_trip()
        
        if not present_trip or not present_trip.legs:
            return {
                "score": "Not valid",
                "route_sequence": [],
                "stop_sequence": []
            }
            
        # Trạm đầu và trạm cuối của hành trình
        start_stop_id = present_trip.legs[0].board_stop_id
        end_stop_id = present_trip.legs[-1].alight_stop_id
        
        cricuity_index = find_cricuity_index_of_a_trip(
            trip=present_trip,
            start_stop_id=start_stop_id,
            end_stop_id=end_stop_id,
            transit_network=transit_network,
            geometry_calculator=geometry_calculator
        )
        
        # Tạo danh sách tuyến và trạm để trả về
        route_sequence = [leg.route_id for leg in present_trip.legs]
        stop_sequence = []
        for leg in present_trip.legs:
            if not stop_sequence:
                stop_sequence.append(leg.board_stop_id)
            if leg.board_stop_id != stop_sequence[-1]:
                stop_sequence.append(leg.board_stop_id)
            stop_sequence.append(leg.alight_stop_id)
            
        return {
            "score": cricuity_index,
            "route_sequence": route_sequence,
            "stop_sequence": stop_sequence
        }
