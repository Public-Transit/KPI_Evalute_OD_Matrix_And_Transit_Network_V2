from dataclasses import dataclass

from src.domain.model.leg import Leg, CandidateLeg 

@dataclass
class Trip:
    legs: list[Leg]

@dataclass
class CandidateTrip:
    candidate_legs: list[CandidateLeg]
