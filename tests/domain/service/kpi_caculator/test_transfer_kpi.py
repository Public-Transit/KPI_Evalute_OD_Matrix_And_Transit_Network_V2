import pytest
from src.domain.service.kpi_caculator.transfer_kpi import TransferRateCalculator
from src.domain.model.routing_result import ODRoutingResult
from src.domain.model.trip import CandidateTrip, Trip
from src.domain.model.leg import CandidateLeg

def test_transfer_rate_calculator():
    calc = TransferRateCalculator()
    
    ct0 = CandidateTrip([CandidateLeg("R1", {"S1"}, {"S2"})])
    res0 = ODRoutingResult("OD1", ct0, Trip([]))
    assert calc.calculate(res0)["score"] == 0
    
    ct1 = CandidateTrip([CandidateLeg("R1", {"S1"}, {"S2"}), CandidateLeg("R2", {"S2"}, {"S3"})])
    res1 = ODRoutingResult("OD1", ct1, Trip([]))
    assert calc.calculate(res1)["score"] == 1
    
    ct2 = CandidateTrip([CandidateLeg("R1", {"S1"}, {"S2"}), CandidateLeg("R2", {"S2"}, {"S3"}), CandidateLeg("R3", {"S3"}, {"S4"})])
    res2 = ODRoutingResult("OD1", ct2, Trip([]))
    assert calc.calculate(res2)["score"] == "Not valid or >1"

    ct_empty = CandidateTrip([])
    res_empty = ODRoutingResult("OD1", ct_empty, Trip([]))
    assert calc.calculate(res_empty)["score"] == "Not valid or >1"
