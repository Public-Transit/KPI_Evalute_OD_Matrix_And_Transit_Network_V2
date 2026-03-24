import pytest
from src.domain.model.leg import Leg, CandidateLeg

def test_leg_creation():
    l = Leg("R1", "S1", "S2")
    assert l.route_id == "R1"
    assert l.board_stop_id == "S1"
    assert l.alight_stop_id == "S2"

def test_candidate_leg_creation():
    cl = CandidateLeg("R1", {"S1", "S2"}, {"S3"})
    assert cl.route_id == "R1"
    assert cl.possible_boarding_stop_ids == {"S1", "S2"}
    assert cl.possible_alighting_stop_ids == {"S3"}
