from abc import ABC, abstractmethod
from typing import Any
from src.domain.model.routing_result_v2 import EvaluatedRoutingOption

class KPICalculator(ABC):
    @abstractmethod
    def calculate(self, evaluated_routing_option: EvaluatedRoutingOption, **kwargs) -> dict[str, Any]:
        """Tính toán KPI dựa trên kết quả tìm đường (ODRoutingResult)"""
        pass
