import pytest
from src.domain.model.trip import Trip, CandidateTrip
from src.domain.model.leg import Leg, CandidateLeg

def test_trip_creation():
    l1 = Leg("R1", "S1", "S2")
    t = Trip([l1])
    assert len(t.legs) == 1
    assert t.legs[0] == l1

def test_candidate_trip_creation():
    cl1 = CandidateLeg("R1", {"S1"}, {"S2"})
    ct = CandidateTrip([cl1])
    assert len(ct.candidate_legs) == 1
    assert ct.candidate_legs[0] == cl1
