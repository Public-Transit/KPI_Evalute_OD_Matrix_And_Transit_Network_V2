from src.domain.service.kpi_caculator.kpi_base import KPICalculator
from src.domain.model.routing_result_v2 import EvaluatedRoutingOption
from src.domain.model.trip import Trip

class TransferRateCalculator(KPICalculator):
    def calculate(self, evaluated_routing_option: EvaluatedRoutingOption, **kwargs) -> dict:
        """
        Tính toán KPI về số lần chuyển tuyến (0 hoặc 1) của chuyến đi đại diện trong 1 phương án di chuyển.
        
        Args:
            evaluated_routing_option (EvaluatedRoutingOption): Phương án di chuyển
            
        Returns:
            dict: Chứa điểm (0 cho đi thẳng, 1 cho 1 lần đổi xe, hoặc "Not valid" nếu lớn hơn)
        """
        representative_trip: Trip = evaluated_routing_option.representative_trip()
        
        if not representative_trip or not representative_trip.legs:
            return {"score": "Not valid or >1", "reason": "No valid trip"}
            
        total_legs = len(representative_trip.legs)
        total_transfers = total_legs - 1
        
        if total_transfers == 0:
            return {"score": 0}
        elif total_transfers == 1:
            return {"score": 1}
        else:
            return {"score": "Not valid or >1"}
