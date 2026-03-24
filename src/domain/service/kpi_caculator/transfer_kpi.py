from src.domain.service.kpi_caculator.kpi_base import KPICalculator
from src.domain.model.routing_result import ODRoutingResult

class TransferRateCalculator(KPICalculator):
    def calculate(self, routing_result: ODRoutingResult, **kwargs) -> dict:
        """
        Tính toán KPI về số lần chuyển tuyến (0 hoặc 1).
        
        Args:
            routing_result (ODRoutingResult): Kết quả tìm đường
            
        Returns:
            dict: Chứa điểm (0 cho đi thẳng, 1 cho 1 lần đổi xe, hoặc "Not valid" nếu lớn hơn)
        """
        present_trip = routing_result.present_trip()
        
        if not present_trip or not present_trip.legs:
            return {"score": "Not valid or >1", "reason": "No valid trip"}
            
        total_legs = len(present_trip.legs)
        total_transfers = total_legs - 1
        
        if total_transfers == 0:
            return {"score": 0}
        elif total_transfers == 1:
            return {"score": 1}
        else:
            return {"score": "Not valid or >1"}
