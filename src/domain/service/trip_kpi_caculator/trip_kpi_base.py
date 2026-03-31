from abc import ABC, abstractmethod
from typing import Any
from src.domain.model.trip import Trip
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.od_matrix import ODMatrix
from src.domain.port import IGeometryCalculator

class TripKPICalculator(ABC):
    @abstractmethod
    def calculate(self, *args, **kwargs) -> Any:
        """Tính toán KPI của 1 cách đi"""
        pass
