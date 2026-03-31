import pytest
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.route import Route
from src.domain.model.stop import Stop
from src.domain.model.point import Point

def test_transit_network_creation():
    s1 = Stop("S1", 0.0, 0.0)
    r1 = Route("R1", [Point(0,0)], ["S1"])
    
    tn = TransitNetwork([s1], [r1])
    
    assert len(tn.routes()) == 1
    assert len(tn.stops()) == 1
    assert tn.get_route_by_id("R1") == r1
    assert tn.get_stop_by_id("S1") == s1
    assert tn.get_route_by_id("NonExistent") is None
