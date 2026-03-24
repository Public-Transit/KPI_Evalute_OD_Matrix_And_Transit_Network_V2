import pytest
from src.domain.service.kpi_caculator.spatial_coverage_kpi import SpatialCoverageCalculator
from src.domain.model.routing_result import ODRoutingResult
from src.domain.model.trip import CandidateTrip, Trip
from src.domain.model.leg import Leg
from src.domain.model.point import Point
from src.domain.model.stop import Stop
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.model.zone import Zone
from tests.domain.mock_geometry import MockGeometryCalculator

def test_spatial_coverage_calculator():
    calc = SpatialCoverageCalculator()
    
    p1 = Point(1, 1)
    p2 = Point(2, 2)
    s1 = Stop("S1", 1.0, 1.0)
    s2 = Stop("S2", 2.0, 2.0)
    tn = TransitNetwork([], [s1, s2])
    
    z1 = Zone("Z1", [], Point(1, 1))
    z2 = Zone("Z2", [], Point(2, 2))
    od1 = ODPair("OD1", "Z1", "Z2", 10)
    matrix = ODMatrix([od1], [z1, z2])
    
    geometry_calc = MockGeometryCalculator()
    
    pt = Trip([Leg("R1", "S1", "S2")])
    res = ODRoutingResult("OD1", CandidateTrip([]), pt)
    
    kpi_res = calc.calculate(
        res, 
        od_matrix=matrix, 
        transit_network=tn, 
        geometry_calculator=geometry_calc, 
        radius_m=500.0
    )
    
    assert kpi_res["score_ratio"] == 0.25
    assert kpi_res["score_percent"] == 25.0
    assert kpi_res["origin_coverage_ratio"] == 0.5
    assert kpi_res["destination_coverage_ratio"] == 0.5
