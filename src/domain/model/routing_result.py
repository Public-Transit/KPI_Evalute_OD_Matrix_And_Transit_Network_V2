class ODRoutingResult:
    def __init__(self, od_pair_id: str, candidate_trip: CandidateTrip, present_trip: Trip):
        self._od_pair_id = od_pair_id
        self._candidate_trip = candidate_trip
        self._present_trip = present_trip

    def od_pair_id(self) -> str:
        return self._od_pair_id
    
    def candidate_trip(self) -> CandidateTrip:
        return self._candidate_trip
    
    def present_trip(self) -> Trip:
        return self._present_trip