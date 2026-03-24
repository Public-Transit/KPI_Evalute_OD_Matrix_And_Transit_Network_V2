import pytest
from src.domain.model.point import Point
from tests.domain.mock_geometry import MockGeometryCalculator

def test_point_creation():
    p = Point(21.0, 105.0)
    assert p.lat() == 21.0
    assert p.lon() == 105.0

def test_point_distance_to():
    p1 = Point(0.0, 0.0)
    p2 = Point(0.0, 1.0)
    calc = MockGeometryCalculator()
    dist = p1.distance_to(p2, calc)
    assert dist > 0
