from typing import Any
from src.domain.service.kpi_caculator.kpi_base import KPICalculator
from src.domain.model.routing_result import ODRoutingResult
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.domain.port import IGeometryCalculator

class SpatialCoverageCalculator(KPICalculator):
    def calculate(self, routing_result: ODRoutingResult, **kwargs) -> dict[str, Any]:
        """
        Tính toán KPI độ bao phủ không gian.
        
        Required kwargs:
            od_matrix (ODMatrix): Cung cấp zone data
            transit_network (TransitNetwork): Cung cấp stop data
            geometry_calculator (IGeometryCalculator): Công cụ tính toán không gian
            radius_m (float): Bán kính vùng phủ quanh trạm (mặc định 500.0)
        """
        od_matrix: ODMatrix = kwargs.get("od_matrix")
        transit_network: TransitNetwork = kwargs.get("transit_network")
        geometry_calculator: IGeometryCalculator = kwargs.get("geometry_calculator")
        radius_m: float = kwargs.get("radius_m", 0.0005)
        
        if not all([od_matrix, transit_network, geometry_calculator]):
            raise ValueError("Cần cung cấp od_matrix, transit_network và geometry_calculator")
            
        present_trip = routing_result.present_trip()
        if not present_trip or not present_trip.legs:
            return {"score_ratio": 0.0, "score_percent": 0.0}
            
        od_pair_id = routing_result.od_pair_id()
        od_pair = od_matrix.get_od_pair_by_id(od_pair_id)
        
        if not od_pair:
            raise ValueError(f"Không tìm thấy OD pair với id {od_pair_id}")
            
        origin_zone = od_matrix.get_zone_by_id(od_pair.origin_zone_id())
        dest_zone = od_matrix.get_zone_by_id(od_pair.destination_zone_id())
        
        # Trạm đầu và trạm cuối
        board_stop_id = present_trip.legs[0].board_stop_id
        alight_stop_id = present_trip.legs[-1].alight_stop_id
        
        origin_stop = transit_network.get_stop_by_id(board_stop_id)
        dest_stop = transit_network.get_stop_by_id(alight_stop_id)
        
        origin_points = [origin_stop.coord()] if origin_stop else []
        origin_coverage_ratio = origin_zone.calculate_zone_coverage_ratio(
            points=origin_points, 
            radius_m=radius_m,
            geometry_calculator=geometry_calculator
        )
        
        dest_points = [dest_stop.coord()] if dest_stop else []
        dest_coverage_ratio = dest_zone.calculate_zone_coverage_ratio(
            points=dest_points, 
            radius_m=radius_m,
            geometry_calculator=geometry_calculator
        )
        
        score_ratio = max(0.0, min(1.0, origin_coverage_ratio * dest_coverage_ratio))
        
        return {
            "score_percent": score_ratio * 100.0,
            "score_ratio": score_ratio,
            "origin_coverage_percent": origin_coverage_ratio * 100.0,
            "origin_coverage_ratio": origin_coverage_ratio,
            "destination_coverage_percent": dest_coverage_ratio * 100.0,
            "destination_coverage_ratio": dest_coverage_ratio,
            "origin_zone_id": origin_zone.id(),
            "destination_zone_id": dest_zone.id(),
            "radius_m": radius_m,
            "origin_stop_count": 1 if origin_stop else 0,
            "destination_stop_count": 1 if dest_stop else 0,
        }
