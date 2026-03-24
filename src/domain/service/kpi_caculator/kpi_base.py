from abc import ABC, abstractmethod
from typing import Any
from src.domain.model.routing_result import ODRoutingResult

class KPICalculator(ABC):
    @abstractmethod
    def calculate(self, routing_result: ODRoutingResult, **kwargs) -> dict[str, Any]:
        """Tính toán KPI dựa trên kết quả tìm đường (ODRoutingResult)"""
        pass
