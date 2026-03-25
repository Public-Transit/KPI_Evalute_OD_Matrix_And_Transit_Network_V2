from src.domain.model.trip import CandidateTrip, Trip

class EvaluatedRoutingOption:
    """
    Đại diện cho 1 phương án di chuyển hoàn chỉnh giữa O và D.
    Bao gồm cái nhìn tổng quan (candidate) và cách đi đại diện/ tối ưu nhất (representative).
    """
    def __init__(self, candidate_trip: CandidateTrip, representative_trip: Trip):
        self._candidate_trip = candidate_trip
        self._representative_trip = representative_trip

    def candidate_trip(self) -> CandidateTrip:
        return self._candidate_trip

    def representative_trip(self) -> Trip:
        return self._representative_trip
    

class ODRoutingResultV2:
    def __init__(self, od_pair_id: str, evaluated_routing_options: list[EvaluatedRoutingOption]):
        self._od_pair_id = od_pair_id
        self._evaluated_routing_options = evaluated_routing_options

    def od_pair_id(self) -> str:
        return self._od_pair_id
    
    def evaluated_routing_options(self) -> list[EvaluatedRoutingOption]:
        return self._evaluated_routing_options
