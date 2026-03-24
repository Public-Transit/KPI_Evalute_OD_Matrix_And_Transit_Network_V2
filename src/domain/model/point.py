from src.domain.port import IGeometryCalculator

class Point:
    def __init__(self, lat: float, lon: float):
        self._lat = lat
        self._lon = lon

    def lat(self) -> float:
        return self._lat
    
    def lon(self) -> float:
        return self._lon
    
    def distance_to(self, other: Point, geometry_calculator: IGeometryCalculator) -> float:
        return geometry_calculator.calculate_distance_between_two_points(self, other)
