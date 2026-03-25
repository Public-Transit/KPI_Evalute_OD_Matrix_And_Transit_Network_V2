import pytest
from src.domain.service.spatial import (
    find_all_routes_pass_through_zone,
    find_all_stops_on_a_route_located_in_a_certain_zone,
    find_cricuity_index_of_a_trip,
    find_closest_stop_to_centroid
)
from src.domain.model.point import Point
from src.domain.model.stop import Stop
from src.domain.model.zone import Zone
from src.domain.model.route import Route
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.trip import Trip
from src.domain.model.leg import Leg
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator



@pytest.fixture
def sample_data():
    p1 = Point(1, 1)
    p2 = Point(2, 2)
    s1 = Stop("S1", 1.0, 1.0)
    s2 = Stop("S2", 2.0, 2.0)
    
    r1 = Route("R1", [p1, p2], ["S1", "S2"])
    
    z1 = Zone("Z1", [Point(0,0), Point(0,3), Point(3,3), Point(3,0)], Point(1.5, 1.5))
    
    tn = TransitNetwork([s1, s2], [r1])
    return z1, tn, r1, s1, s2

def test_find_all_routes_pass_through_zone(sample_data):
    z1, tn, r1, s1, s2 = sample_data
    calc = ShapelyGeometryCalculator
()
    routes = find_all_routes_pass_through_zone(z1, tn, calc)
    assert len(routes) == 1
    assert routes[0].id() == "R1"

def test_find_all_stops_on_a_route_located_in_a_certain_zone(sample_data):
    z1, tn, r1, s1, s2 = sample_data
    calc = ShapelyGeometryCalculator
()
    stops = find_all_stops_on_a_route_located_in_a_certain_zone(z1, r1, tn, calc)
    assert len(stops) == 2

def test_find_cricuity_index_of_a_trip(sample_data):
    z1, tn, r1, s1, s2 = sample_data
    calc = ShapelyGeometryCalculator
()
    trip = Trip([Leg("R1", "S1", "S2")])
    index = find_cricuity_index_of_a_trip(trip, "S1", "S2", tn, calc)
    assert index > 0

def test_find_closest_stop_to_centroid(sample_data):
    z1, tn, r1, s1, s2 = sample_data
    calc = ShapelyGeometryCalculator
()
    stop = find_closest_stop_to_centroid(z1, tn, calc)
    assert stop is not None
