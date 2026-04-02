import pytest
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.trip import Trip, CandidateTrip
from src.domain.model.leg import Leg, CandidateLeg
from src.domain.model.route import Route
from src.domain.model.point import Point
from src.domain.model.stop import Stop
from src.domain.service.spatial import find_intersecting_trip_between_candidatetrip_and_trip

@pytest.fixture
def sample_network():
    # Setup a simple transit network for testing
    # Route R1: S1 -> S2 -> S3 -> S4 -> S5
    r1_stops = ["S1", "S2", "S3", "S4", "S5"]
    r1 = Route(route_id="R1", shape=[], stops=r1_stops)
    
    # Route R2: S10 -> S3 -> S4 -> S11 -> S12  (Shares S3, S4 with R1)
    r2_stops = ["S10", "S3", "S4", "S11", "S12"]
    r2 = Route(route_id="R2", shape=[], stops=r2_stops)
    
    # Needs valid Stop objects in the network for get_stop_by_id
    stops = []
    for s_id in list(set(r1_stops + r2_stops)):
        stops.append(Stop(stop_id=s_id, lat=0.0, lon=0.0))
        
    return TransitNetwork(stops=stops, routes=[r1, r2])

def test_0_transfer_partial_intersection(sample_network):
    """
    Test 0 lần chuyển tuyến: Giao 1 phần (nằm giữa).
    Trip chạy trên R1 từ S1 đến S5.
    Candidate muốn đi từ {S2} đến {S4}.
    Kết quả mong đợi: Lấy đoạn S2 -> S4.
    """
    trip = Trip(legs=[Leg("R1", "S1", "S5")])
    c_leg = CandidateLeg("R1", {"S2"}, {"S4"})
    candidate_trip = CandidateTrip([c_leg])
    
    result = find_intersecting_trip_between_candidatetrip_and_trip(candidate_trip, trip, sample_network)
    
    assert len(result) == 1
    assert result[0].legs[0].board_stop_id == "S2"
    assert result[0].legs[0].alight_stop_id == "S4"



def test_0_transfer_boundary_intersection(sample_network):
    # Trip chạy từ S3 đến S4
    trip = Trip(legs=[Leg("R1", "S3", "S4")])
    
    # Biên đầu: Khách có thể lên ở {S2, S3} và xuống ở {S3}
    # (S3 là điểm giao duy nhất vì S2 không nằm trong lộ trình S3-S4 của Trip)
    c_leg1 = CandidateLeg("R1", {"S1"}, {"S3"}) 
    res1 = find_intersecting_trip_between_candidatetrip_and_trip(CandidateTrip([c_leg1]), trip, sample_network)
    assert len(res1) == 1
    assert res1[0].legs[0].board_stop_id == "S3"
    assert res1[0].legs[0].alight_stop_id == "S3"
    
    # Biên cuối: Khách lên ở {S4} và xuống ở {S4, S5}
    c_leg2 = CandidateLeg("R1", {"S4"}, {"S5"})
    res2 = find_intersecting_trip_between_candidatetrip_and_trip(CandidateTrip([c_leg2]), trip, sample_network)
    assert len(res2) == 1
    assert res2[0].legs[0].board_stop_id == "S4"
    assert res2[0].legs[0].alight_stop_id == "S4"


def test_0_transfer_no_intersection(sample_network):
    """
    Test 0 lần chuyển tuyến: Không giao nhau.
    Trip chạy trên R1 từ S1 đến S2.
    Candidate muốn đi từ {S3} đến {S4}.
    Kết quả: Rỗng.
    """
    trip = Trip(legs=[Leg("R1", "S1", "S2")])
    c_leg = CandidateLeg("R1", {"S3"}, {"S4"})
    
    result = find_intersecting_trip_between_candidatetrip_and_trip(CandidateTrip([c_leg]), trip, sample_network)
    assert len(result) == 0

def test_1_transfer_partial_intersection(sample_network):
    """
    Test 1 lần chuyển tuyến: Giao 1 phần.
    Trip: 2 leg nối tiếp có chuyển tuyến thực tế tại S4. S1->S4(R1) và S4->S12(R2).
    Candidate: Chuyển tuyến tại S4. Đi từ {S2}->{S4}(R1) và {S4}->{S11}(R2).
    Candidate đảm bảo alight của leg trước trùng board của leg sau (đều có S4).
    Kết quả: Giao 1 phần là S2->S4(R1) và S4->S11(R2).
    """
    trip = Trip(legs=[Leg("R1", "S1", "S4"), Leg("R2", "S4", "S12")])
    
    c_leg1 = CandidateLeg("R1", {"S2"}, {"S4"})
    c_leg2 = CandidateLeg("R2", {"S4"}, {"S11"})
    candidate_trip = CandidateTrip([c_leg1, c_leg2])
    
    result = find_intersecting_trip_between_candidatetrip_and_trip(candidate_trip, trip, sample_network)
    assert len(result) == 1
    res_trip = result[0]
    assert len(res_trip.legs) == 2
    assert res_trip.legs[0].board_stop_id == "S2"
    assert res_trip.legs[0].alight_stop_id == "S4"
    assert res_trip.legs[1].board_stop_id == "S4"
    assert res_trip.legs[1].alight_stop_id == "S11"

def test_1_transfer_boundary_intersection(sample_network):
    """
    Test 1 lần chuyển tuyến: Giao ở biên giới hạn chuyến.
    Trip: S2->S4(R1) và S4->S11(R2) (Trạm nối là S4).
    Candidate: Bắt đầu từ ngoài Trip (S1), kết thúc ngoài Trip (S12). Chuyển tuyến tại S4.
               Candidate: S1 hoặc S2 -> S4 (R1), S4 -> S11 hoặc S12 (R2).
    Candidate đảm bảo alight(L1) intersect board(L2) là {S4}.
    Kết quả: Chỉ lấy được đoạn giới hạn bởi Trip (S2->S4 và S4->S11).
    """
    trip = Trip(legs=[Leg("R1", "S2", "S4"), Leg("R2", "S4", "S11")])
    
    c_leg1 = CandidateLeg("R1", {"S1", "S2"}, {"S4"})
    c_leg2 = CandidateLeg("R2", {"S4"}, {"S11", "S12"})
    candidate_trip = CandidateTrip([c_leg1, c_leg2])
    
    result = find_intersecting_trip_between_candidatetrip_and_trip(candidate_trip, trip, sample_network)
    assert len(result) == 1
    res_trip = result[0]
    assert len(res_trip.legs) == 2
    assert res_trip.legs[0].board_stop_id == "S2"
    assert res_trip.legs[0].alight_stop_id == "S4"
    assert res_trip.legs[1].board_stop_id == "S4"
    assert res_trip.legs[1].alight_stop_id == "S11"

def test_1_transfer_no_intersection(sample_network):
    """
    Test 1 lần chuyển tuyến: Không giao nhau (chuyển tuyến không khớp).
    Trip: S1->S3(R1) và S3->S12(R2) (Chuyển tại S3).
    Candidate: Yêu cầu chuyển tại S4. Leg1 muốn đến S4 trên R1, Leg2 đón ở S4 trên R2.
    Kết quả: Trip không chạy đến S4 theo R1, nên không khớp.
    """
    trip = Trip(legs=[Leg("R1", "S1", "S3"), Leg("R2", "S3", "S12")])
    
    c_leg1 = CandidateLeg("R1", {"S1"}, {"S4"})
    c_leg2 = CandidateLeg("R2", {"S4"}, {"S12"})
    candidate_trip = CandidateTrip([c_leg1, c_leg2])
    
    result = find_intersecting_trip_between_candidatetrip_and_trip(candidate_trip, trip, sample_network)
    assert len(result) == 0
