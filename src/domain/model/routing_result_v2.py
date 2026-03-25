class ODRoutingResultV2:
    def __init__(self, od_pair_id: str, candidate_trips: List[CandidateTrip], present_trips: List[Trip]):
        self._od_pair_id = od_pair_id
        self._candidate_trips = candidate_trip
        self._present_trips = present_trip

    def od_pair_id(self) -> str:
        return self._od_pair_id
    
    def candidate_trips(self) -> List[CandidateTrip]:
        return self._candidate_trip
    
    def present_trips(self) -> Trip:
        return self._present_trip