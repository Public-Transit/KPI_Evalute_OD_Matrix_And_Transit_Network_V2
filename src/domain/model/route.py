from __future__ import annotations
from typing import TYPE_CHECKING
from src.domain.model.point import Point

if TYPE_CHECKING:
    from src.domain.model.stop import Stop
    from src.domain.port import IGeometryCalculator

class Route:
    def __init__(self, route_id: str, shape: list[Point], stops: list[str]):
        self._id = route_id
        self._shape = shape
        self._stops = stops

    def id(self) -> str:
        return self._id
    
    def shape(self) -> list[Point]:
        return self._shape
    
    def stops_seq(self) -> list[str]:
        return self._stops

    def get_distance_between_two_stops(self, start_stop: Stop, end_stop: Stop, geometry_calculator: IGeometryCalculator) -> float:
        return geometry_calculator.calc_distance_between_two_stops_in_route(self, start_stop, end_stop)

    def get_cricuity_index_between_two_stops(self, start_stop: Stop, end_stop: Stop, geometry_calculator: IGeometryCalculator) -> float:
        return geometry_calculator.calculate_cricuity_index_between_two_stops_in_route(self, start_stop, end_stop)
    
    def get_shared_stops_with_other_route(self, other_route: Route, geometry_calculator: IGeometryCalculator) -> list[Stop]:
        return geometry_calculator.get_shared_stops_two_routes(self, other_route)


        