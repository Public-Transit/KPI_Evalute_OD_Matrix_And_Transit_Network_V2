import geopy
import geopy.distance
import shapely
import shapely.geometry
from shapely.ops import substring

from src.domain.port import IGeometryCalculator
from src.domain.model.point import Point
from src.domain.model.zone import Zone
from src.domain.model.route import Route
from src.domain.model.stop import Stop


def as_geopy(p: Point):
    return geopy.Point(p.lat(), p.lon())

def as_shapely(p: Point):
    return shapely.Point(p.lat(), p.lon())

def as_shapely_linestring(p_list: list[Point]):
    if len(p_list) < 2:
        raise ValueError("List of points must contain at least 2 points")
    else:
        return shapely.geometry.LineString([as_shapely(p) for p in p_list])

def as_shapely_polygon(p_list: list[Point]):
    if len(p_list) < 3:
        raise ValueError("List of points must contain at least 3 points")
    else:
        return shapely.geometry.Polygon([as_shapely(p) for p in p_list])

class ShapelyGeometryCalculator(IGeometryCalculator):
    def calculate_distance_between_two_points(self, p1: Point, p2: Point) -> float:
        return geopy.distance.geodesic(as_geopy(p1), as_geopy(p2)).meters

    def calculate_distance_between_point_and_line(self, p: Point, line_start_point: Point, line_end_point: Point) -> float:
        line = as_shapely_linestring([as_shapely(line_start_point), as_shapely(line_end_point)])
        point = as_shapely(p)
        # Khoảng cách ở đây là theo hệ tọa độ độ (degrees). 
        # Để chính xác ra mét, sau này có thể chiếu sang hệ UTM (CRS EPSG:32648 cho VN).
        return point.as_shapely.distance(line)

    def calc_distance_between_two_stops_in_route(self, route: Route, start_stop: Stop, end_stop: Stop) -> float:
        
        route_linestring = as_shapely_linestring(route.shape())
        start_stop_point = as_shapely(start_stop.coord())
        end_stop_point = as_shapely(end_stop.coord())
            
        # Tìm hình chiếu của stop lên tuyến đường (ở khoảng cách nào trên toàn tuyến)
        dist_start = route_linestring.project(start_stop_point)
        dist_end = route_linestring.project(end_stop_point)
        
        min_dist = min(dist_start, dist_end)
        max_dist = max(dist_start, dist_end)
        
        # Lấy đoạn phụ (sub-line) nằm giữa 2 hình chiếu dọc theo hành trình
        sub_line = substring(route_linestring, min_dist, max_dist)
        
        # Nếu cắt không thành công hoặc chỉ là 1 điểm
        if not sub_line or sub_line.is_empty or sub_line.geom_type == 'Point':
            return 0.0
            
        real_distance = 0.0
        coords = list(sub_line.coords)
        for i in range(len(coords) - 1):
            p1 = (coords[i][0], coords[i][1]) # (lat, lon)
            p2 = (coords[i+1][0], coords[i+1][1])
            real_distance += geopy.distance.geodesic(p1, p2).meters
            
        return real_distance

    def calculate_cricuity_index_between_two_stops_in_route(self, route: Route, start_stop: Stop, end_stop: Stop) -> float:
        route_dist = self.calc_distance_between_two_stops_in_route(route, start_stop, end_stop)
        straight_dist = self.calculate_distance_between_two_points(start_stop.coord(), end_stop.coord())
        if straight_dist == 0:
            return 1.0 # Tránh lỗi chia cho 0
        return route_dist / straight_dist

    def get_shared_stops_two_routes(self, route1: Route, route2: Route) -> list[str]:
        my_stop_ids = set(route1.stops_seq())
        other_stop_ids = set(route2.stops_seq())
        
        # Phép & (intersection) của Set trong Python
        shared_ids = my_stop_ids & other_stop_ids 
    
        return [stop for stop in route1.stops_seq() if stop in shared_ids]

    def is_point_in_zone(self, point: Point, zone: Zone) -> bool:
        polygon = as_shapely_polygon(zone.boundary())
        return polygon.contains(as_shapely(point))

    def calculate_zone_coverage_ratio(self, zone: Zone, points: list[Point], radius_m: float) -> float:
        import math
        import shapely.ops

        if not zone.boundary() or len(zone.boundary()) < 3:
            return 0.0

        EARTH_RADIUS_M = 6_371_008.8
        centroid = zone.centroid()
        lat0_rad = math.radians(centroid.lat())

        def to_local_xy(point: Point, origin: Point):
            delta_lat_rad = math.radians(point.lat() - origin.lat())
            delta_lon_rad = math.radians(point.lon() - origin.lon())
            x = EARTH_RADIUS_M * delta_lon_rad * math.cos(lat0_rad)
            y = EARTH_RADIUS_M * delta_lat_rad
            return x, y

        local_boundary = [to_local_xy(p, centroid) for p in zone.boundary()]
        local_zone_polygon = shapely.geometry.Polygon(local_boundary)
        
        if local_zone_polygon.is_empty:
            return 0.0

        if not local_zone_polygon.is_valid:
            local_zone_polygon = local_zone_polygon.buffer(0)

        zone_area = local_zone_polygon.area
        if zone_area <= 0:
            return 0.0

        stop_buffers = []
        for p in points:
            x, y = to_local_xy(p, centroid)
            stop_buffers.append(shapely.geometry.Point(x, y).buffer(radius_m))

        if not stop_buffers:
            return 0.0

        covered_by_stops = shapely.ops.unary_union(stop_buffers)
        if covered_by_stops.is_empty:
            return 0.0

        covered_inside_zone = covered_by_stops.intersection(local_zone_polygon)
        if covered_inside_zone.is_empty:
            return 0.0

        return max(0.0, min(1.0, covered_inside_zone.area / zone_area))