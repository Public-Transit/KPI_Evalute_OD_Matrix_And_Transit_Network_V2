from src.domain.model.trip import CandidateTrip, Trip

class ODRoutingResultV2:
    def __init__(self, od_pair_id: str, candidate_trips: list[CandidateTrip], present_trips: list[Trip]):
        self._od_pair_id = od_pair_id
        self._candidate_trips = candidate_trips
        self._present_trips = present_trips
        self._best_trip = None

    def od_pair_id(self) -> str:
        return self._od_pair_id
    
    def candidate_trips(self) -> list[CandidateTrip]:
        return self._candidate_trips
    
    def present_trips(self) -> list[Trip]:
        return self._present_trips

    def set_best_trip(self, best_trip: Trip):
        self._best_trip = best_trip

    def get_best_trip(self) -> Trip:
        return self._best_trip