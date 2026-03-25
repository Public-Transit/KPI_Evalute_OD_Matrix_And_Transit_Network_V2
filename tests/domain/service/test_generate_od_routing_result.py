import pytest
from src.domain.service.generate_od_routing_result import GenerateODRoutingResultService
from src.domain.service.routing import AbstractRouting
from src.domain.service.filter_v2 import AbstractCandidateTripFilterV2
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.routing_result_v2 import ODRoutingResultV2
from src.domain.model.trip import CandidateTrip, Trip
from src.domain.model.leg import CandidateLeg, Leg
from src.domain.model.point import Point
from src.domain.model.stop import Stop
from src.domain.model.route import Route
from src.domain.model.zone import Zone
from src.domain.model.od_pair import ODPair
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator

class MockRoutingEngine(AbstractRouting):
    def __init__(self, expected_trips):
        self._expected_trips = expected_trips
        
    def find_candidate_trips_for_od_pair(self, od_pair, od_matrix, transit_network, geometry_calculator):
        return self._expected_trips

class MockFilterEngine(AbstractCandidateTripFilterV2):
    def __init__(self, expected_pt):
        self._expected_pt = expected_pt
        
    def filter(self, od_pair, od_matrix, transit_network, candidate_trip, geometry_calculator):
        return self._expected_pt

def test_generate_od_routing_result_service():
    # Setup mock domain data
    p1 = Point(1, 1)
    s1 = Stop("S1", 1.0, 1.0)
    s2 = Stop("S2", 2.0, 2.0)
    r1 = Route("R1", [p1, Point(2,2)], ["S1", "S2"])
    
    # Needs 4 points for valid boundaries in shapely
    z1 = Zone("Z1", [Point(0,0), Point(0,2), Point(2,2), Point(2,0)], Point(1, 1))
    z2 = Zone("Z2", [Point(2,2), Point(2,4), Point(4,4), Point(4,2)], Point(3, 3))
    od = ODPair("OD1", "Z1", "Z2", 10)
    
    matrix = ODMatrix([od], [z1, z2])
    tn = TransitNetwork([s1, s2], [r1])
    
    ct1 = CandidateTrip([CandidateLeg("R1", {"S1"}, {"S2"})])
    pt1 = Trip([Leg("R1", "S1", "S2")])
    
    # Configure mock services
    routing_mock = MockRoutingEngine([ct1])
    filter_mock = MockFilterEngine(pt1)
    
    geo_calc = ShapelyGeometryCalculator()
    
    # Test execution
    service = GenerateODRoutingResultService(routing_mock, filter_mock)
    results = service.generate_od_routing_result(matrix, tn, geo_calc)
    
    # Assertions
    assert len(results) == 1
    assert isinstance(results[0], ODRoutingResultV2)
    assert results[0].od_pair_id() == "OD1"
    
    opts = results[0].evaluated_routing_options()
    assert len(opts) == 1
    assert opts[0].candidate_trip() == ct1
    assert opts[0].representative_trip() == pt1
