from dataclasses import dataclass

from src.domain.model.leg import Leg, CandidateLeg 

@dataclass
class Trip:
    legs: list[Leg]

@dataclass
class CandidateTrip:
    candidate_legs: list[CandidateLeg]

    @property
    def possible_boarding_stops_id(self) -> list[str]:
        return self.candidate_legs[0].possible_boarding_stop_ids
    
    @property
    def possible_alighting_stopa_id(self) -> list[str]:
        return self.candidate_legs[-1].possible_alighting_stop_ids
