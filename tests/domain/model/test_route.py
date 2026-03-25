import pytest
from src.domain.model.route import Route
from src.domain.model.point import Point
from src.domain.model.stop import Stop
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator



def test_route_creation():
    r = Route("R1", [Point(0,0), Point(1,1)], ["S1", "S2"])
    assert r.id() == "R1"
    assert len(r.shape()) == 2
    assert r.stops_seq() == ["S1", "S2"]
    
def test_route_geometry_methods():
    r1 = Route("R1", [Point(0,0), Point(1,1)], ["S1", "S2", "S3"])
    r2 = Route("R2", [Point(0,0), Point(1,1)], ["S2", "S3", "S4"])
    s1 = Stop("S1", 0.0, 0.0)
    s2 = Stop("S2", 1.0, 1.01)
    calc = ShapelyGeometryCalculator()
    
    assert r1.get_distance_between_two_stops(s1, s2, calc) > 0
    assert r1.get_cricuity_index_between_two_stops(s1, s2, calc) <1
    
    shared = r1.get_shared_stops_with_other_route(r2, calc)
    assert set(shared) == {"S2", "S3"}
