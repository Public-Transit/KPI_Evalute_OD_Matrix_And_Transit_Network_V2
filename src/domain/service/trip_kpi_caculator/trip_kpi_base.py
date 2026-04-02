from abc import ABC, abstractmethod
from typing import Any
from src.domain.model.trip import Trip
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.od_matrix import ODMatrix
from src.domain.port import IGeometryCalculator
from src.domain.service.routing import AbstractRouting

class TripKPICalculator(ABC):
    @abstractmethod
    def calculate(
        self, 
        trip: Trip, 
        transit_network: TransitNetwork, 
        od_matrix: ODMatrix, 
        routing_engine: AbstractRouting,
        geometry_calculator: IGeometryCalculator 
    ) -> float:
        pass