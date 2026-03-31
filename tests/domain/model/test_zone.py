import pytest
from src.domain.model.zone import Zone
from src.domain.model.point import Point
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator



@pytest.fixture
def sample_zone():
    centroid = Point(1.0, 1.0)
    boundary = [Point(0,0), Point(0,2), Point(2,2), Point(2,0)]
    return Zone("Z01", boundary, centroid)

def test_zone_creation(sample_zone):
    assert sample_zone.id() == "Z01"
    assert sample_zone.centroid().lat() == 1.0
    assert len(sample_zone.boundary()) == 4

def test_is_point_in_zone(sample_zone):
    calc = ShapelyGeometryCalculator()

    # Mock return lat > 0
    p_inside = Point(1.0, 1.0)
    p_outside = Point(-1.0, -1.0)
    
    assert sample_zone.is_point_in_zone(p_inside, calc) is True
    assert sample_zone.is_point_in_zone(p_outside, calc) is False

def test_calculate_zone_coverage_ratio(sample_zone):
    calc = ShapelyGeometryCalculator()
    points = [Point(1.0, 1.0)]
    ratio = sample_zone.calculate_zone_coverage_ratio(points, 500.0, calc)
    assert ratio >= 0.0
