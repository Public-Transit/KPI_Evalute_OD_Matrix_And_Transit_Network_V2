import pytest
from src.domain.model.routing_result import ODRoutingResult
from src.domain.model.trip import Trip, CandidateTrip
from src.domain.model.leg import Leg, CandidateLeg

def test_od_routing_result_creation():
    ct = CandidateTrip([CandidateLeg("R1", {"S1"}, {"S2"})])
    pt = Trip([Leg("R1", "S1", "S2")])
    
    res = ODRoutingResult("OD1", ct, pt)
    
    assert res.od_pair_id() == "OD1"
    assert res.candidate_trip() == ct
    assert res.present_trip() == pt
