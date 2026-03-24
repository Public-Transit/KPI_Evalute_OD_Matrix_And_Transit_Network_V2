from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from src.domain.model.od_pair import ODPair
    from src.domain.model.zone import Zone
    from src.domain.model.trip import Trip
    from src.domain.model.route import Route
    from src.domain.model.stop import Stop
    from src.domain.model.point import Point

class IGeometryCalculator(ABC):
    @abstractmethod
    def calculate_distance_between_two_points(self, p1: Point, p2: Point) -> float:
        pass
    
    @abstractmethod
    def calculate_distance_between_point_and_line(self, p: Point, line_start_point: Point, line_end_point: Point) -> float:
        pass

    @abstractmethod
    def calc_distance_between_two_stops_in_route(self, route: Route, start_stop: Stop, end_stop: Stop) -> float:
        pass

    @abstractmethod
    def calculate_cricuity_index_between_two_stops_in_route(self, route: Route, start_stop: Stop, end_stop: Stop) -> float:
        pass

    @abstractmethod
    def get_shared_stops_two_routes(self, route1: Route, route2: Route) -> list[Stop]:
        pass

    @abstractmethod
    def is_point_in_zone(self, point: Point, zone: Zone) -> bool:
        pass

    @abstractmethod
    def calculate_zone_coverage_ratio(self, zone: Zone, points: list[Point], radius_m: float) -> float:
        pass

