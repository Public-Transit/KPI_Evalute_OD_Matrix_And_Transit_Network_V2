import pytest
from src.domain.service.filter import FilterStrategy
from src.domain.model.point import Point
from src.domain.model.zone import Zone
from src.domain.model.stop import Stop
from src.domain.model.route import Route
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.model.trip import CandidateTrip
from src.domain.model.leg import CandidateLeg
from tests.domain.mock_geometry import MockGeometryCalculator

def test_filter_strategy_0_transfer():
    p1 = Point(1, 1)
    p2 = Point(2, 2)
    s1 = Stop("S1", 1.0, 1.0)
    s2 = Stop("S2", 2.0, 2.0)
    r1 = Route("R1", [p1, p2], ["S1", "S2"])
    tn = TransitNetwork([s1, s2], [r1])
    
    z1 = Zone("Z1", [], Point(1, 1))
    z2 = Zone("Z2", [], Point(2, 2))
    od1 = ODPair("OD1", "Z1", "Z2", 10)
    matrix = ODMatrix([od1], [z1, z2])
    
    ct = CandidateTrip([CandidateLeg("R1", {"S1"}, {"S2"})])
    
    calc = MockGeometryCalculator()
    f = FilterStrategy()
    
    res_trip = f.filter(od1, matrix, tn, ct, calc)
    
    assert res_trip is not None
    assert len(res_trip.legs) == 1
    assert res_trip.legs[0].route_id == "R1"
