import pytest
from src.domain.model.routing_result_v2 import ODRoutingResultV2, EvaluatedRoutingOption
from src.domain.model.trip import Trip, CandidateTrip
from src.domain.model.leg import Leg, CandidateLeg

def test_od_routing_result_creation():
    ct = CandidateTrip([CandidateLeg("R1", {"S1"}, {"S2"})])
    pt = Trip([Leg("R1", "S1", "S2")])
    
    opt = EvaluatedRoutingOption(ct, pt)
    
    assert opt.candidate_trip() == ct
    assert opt.representative_trip() == pt
    
    res = ODRoutingResultV2("OD1", [opt])
    
    assert res.od_pair_id() == "OD1"
    assert len(res.evaluated_routing_options()) == 1
    assert res.evaluated_routing_options()[0] == opt
