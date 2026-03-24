from dataclasses import dataclass

@dataclass
class Leg:
    route_id: str
    board_stop_id: str
    alight_stop_id: str

@dataclass
class CandidateLeg:
    route_id: str
    possible_boarding_stop_ids: set[str]
    possible_alighting_stop_ids: set[str]
    
    
