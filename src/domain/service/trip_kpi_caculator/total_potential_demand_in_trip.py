from src.domain.service.trip_kpi_caculator.trip_kpi_base import TripKPICalculator
from src.domain.service.spatial import get_served_od_pairs_from_segment
from src.domain.model.trip import Trip
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.od_matrix import ODMatrix
from src.domain.port import IGeometryCalculator

class TotalPotentialDemandInTripCalculator(TripKPICalculator):
    def calculate(self, trip: Trip, transit_network: TransitNetwork, od_matrix: ODMatrix, geometry_calculator: IGeometryCalculator) -> float:
        """
        Tính toán KPI về tổng nhu cầu tiềm năng được thỏa mãn bởi 1 cách đi (Trip).
        Bằng cách tập hợp tất cả các cặp OD có quãng đường overlap với bất kỳ đoạn tuyến nào trong hành trình.
        """
        served_od_pairs = set()

        # Quét trực tiếp các Leg trong cách đi
        for leg in trip.legs:
            od_served_by_leg = get_served_od_pairs_from_segment(
                route_id=leg.route_id, 
                start_stop_id=leg.board_stop_id, 
                end_stop_id=leg.alight_stop_id, 
                od_matrix=od_matrix, 
                transit_network=transit_network, 
                geometry_calculator=geometry_calculator
            )
            served_od_pairs.update(od_served_by_leg)

        # Tính tổng nhu cầu (tách trùng lặp do dùng kiểu Set)
        total_potential_demand = sum(od_pair.demand() for od_pair in served_od_pairs)

        return float(total_potential_demand)
