from typing import Tuple
from src.domain.model.point import Point
from src.domain.model.stop import Stop
from src.domain.model.route import Route
from src.domain.model.zone import Zone
from src.domain.model.od_pair import ODPair
from src.domain.model.trip import Trip
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.adapters.repository.abstract_repository import AbstractRepository

class FakeRepoL1(AbstractRepository):
    """
    Level 1: Tối giản nhất (Chỉ 1 route đi thẳng)
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)

        self.zones = [
            Zone("Z1", [P(0,0), P(100,0), P(100,100), P(0,100)], P(50,50)),
            Zone("Z2", [P(300,0), P(400,0), P(400,100), P(300,100)], P(350,50))
        ]
        
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [S("S1", 50, 50), S("S2", 350, 50)]
        self.routes = [Route("R_Direct", [P(50,50), P(350,50)], ["S1", "S2"])]
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
