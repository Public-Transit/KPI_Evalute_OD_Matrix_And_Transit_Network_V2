import pytest
from src.domain.service.kpi_caculator.circuity_kpi import CircuityIndexCalculator
from src.domain.model.routing_result import EvaluatedRoutingOption
from src.domain.model.trip import CandidateTrip, Trip
from src.domain.model.leg import Leg
from src.domain.model.point import Point
from src.domain.model.stop import Stop
from src.domain.model.route import Route
from src.domain.model.transit_network import TransitNetwork
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator



def test_circuity_index_calculator():
    calc = CircuityIndexCalculator()
    
    p1 = Point(1, 1)
    p2 = Point(2, 2)
    s1 = Stop("S1", 1.0, 1.0)
    s2 = Stop("S2", 2.0, 2.0)
    r1 = Route("R1", [p1, p2], ["S1", "S2"])
    tn = TransitNetwork([s1, s2], [r1])
    
    geometry_calc = ShapelyGeometryCalculator()
    
    pt = Trip([Leg("R1", "S1", "S2")])
    res = EvaluatedRoutingOption(CandidateTrip([]), pt)
    
    kpi_res = calc.calculate(res, transit_network=tn, geometry_calculator=geometry_calc)
    
    assert kpi_res["score"] > 0
    assert kpi_res["route_sequence"] == ["R1"]
    assert kpi_res["stop_sequence"] == ["S1", "S2"]
