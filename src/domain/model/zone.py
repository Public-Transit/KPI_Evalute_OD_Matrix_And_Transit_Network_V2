from __future__ import annotations
from typing import TYPE_CHECKING
from src.domain.model.point import Point

if TYPE_CHECKING:
    from src.domain.port import IGeometryCalculator

class Zone:
    def __init__(self, zone_id: str, boundary: list[Point], centroid: Point):
        self._id = zone_id
        self._boundary = boundary
        self._centroid = centroid

    def id(self) -> str:
        return self._id
    
    def boundary(self) -> list[Point]:
        return self._boundary
    
    def centroid(self) -> Point:
        return self._centroid

    def is_point_in_zone(self, point: Point, geometry_calculator: IGeometryCalculator) -> bool:
        return geometry_calculator.is_point_in_zone(point, self)

    def calculate_zone_coverage_ratio(self, points: list[Point], radius_m: float, geometry_calculator: IGeometryCalculator) -> float:
        return geometry_calculator.calculate_zone_coverage_ratio(self, points, radius_m)