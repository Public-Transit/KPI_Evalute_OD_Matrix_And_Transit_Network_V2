import pytest
from src.domain.service.routing import DirectConnectionRouting, OneTransferRoutingEngine
from src.domain.model.point import Point
from src.domain.model.zone import Zone
from src.domain.model.stop import Stop
from src.domain.model.route import Route
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator



@pytest.fixture
def routing_data():
    p1 = Point(1, 1)
    p2 = Point(2, 2)
    p3 = Point(3, 3)
    
    s1 = Stop("S1", 1.0, 1.0)
    s2 = Stop("S2", 2.0, 2.0)
    s3 = Stop("S3", 3.0, 3.0)
    
    r1 = Route("R1", [p1, p2, p3], ["S1", "S2", "S3"])
    r2 = Route("R2", [p1, p2], ["S1", "S2"])
    r3 = Route("R3", [p2, p3], ["S2", "S3"])
    
    tn = TransitNetwork([s1, s2, s3], [r1, r2, r3])
    
    z1 = Zone("Z1", [], Point(1, 1))
    z2 = Zone("Z3", [], Point(3, 3))
    od1 = ODPair("OD1", "Z1", "Z3", 10)
    matrix = ODMatrix([od1], [z1, z2])
    
    return od1, matrix, tn

def test_direct_connection_routing(routing_data):
    od1, matrix, tn = routing_data
    calc = ShapelyGeometryCalculator
()
    router = DirectConnectionRouting()
    
    trips = router.find_candidate_trips_for_od_pair(od1, matrix, tn, calc)
    assert isinstance(trips, list)

def test_one_transfer_routing(routing_data):
    od1, matrix, tn = routing_data
    calc = ShapelyGeometryCalculator
()
    router = OneTransferRoutingEngine()
    
    trips = router.find_candidate_trips_for_od_pair(od1, matrix, tn, calc)
    assert isinstance(trips, list)
