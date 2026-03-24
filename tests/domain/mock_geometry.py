from src.domain.port import IGeometryCalculator
from src.domain.model.point import Point
from src.domain.model.zone import Zone
from src.domain.model.route import Route
from src.domain.model.stop import Stop

class MockGeometryCalculator(IGeometryCalculator):
    def calculate_distance_between_two_points(self, p1: Point, p2: Point) -> float:
        # Distance mock for testing
        return ((p1.lat() - p2.lat())**2 + (p1.lon() - p2.lon())**2)**0.5 * 111320
        
    def calculate_distance_between_point_and_line(self, p: Point, line_start: Point, line_end: Point) -> float:
        return 0.0
        
    def calc_distance_between_two_stops_in_route(self, route: Route, start_stop: Stop, end_stop: Stop) -> float:
        return self.calculate_distance_between_two_points(start_stop.coord(), end_stop.coord()) * 1.5
        
    def calculate_cricuity_index_between_two_stops_in_route(self, route: Route, start_stop: Stop, end_stop: Stop) -> float:
        return 1.2
        
    def get_shared_stops_two_routes(self, route1: Route, route2: Route) -> list[str]:
        # Return intersection of stop IDs
        return list(set(route1.stops_seq()).intersection(set(route2.stops_seq())))
        
    def is_point_in_zone(self, point: Point, zone: Zone) -> bool:
        # Simple mock: return True if point lat > 0 just as a dummy condition
        return point.lat() > 0

    def calculate_zone_coverage_ratio(self, zone: Zone, points: list[Point], radius_m: float) -> float:
        return 0.5
