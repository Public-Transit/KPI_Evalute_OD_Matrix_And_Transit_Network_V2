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

class FakeRepoF4(AbstractRepository):
    """
    Filter Case 4: O/D Priority Selection
    Test việc tự động bỏ qua trạm xa tâm vùng O/D.
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)

        self.zones = [
            Zone("Z1", [P(0,0), P(100,0), P(100,100), P(0,100)], P(50,50)),
            Zone("Z_Hub", [P(200,0), P(300,0), P(300,100), P(200,100)], P(250,50)),
            Zone("Z2", [P(400,0), P(500,0), P(500,100), P(400,100)], P(450,50))
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            S("S1_Far", 10, 50), S("S1_Close", 40, 50),
            S("T1", 250, 50),
            S("S2_Close", 460, 50), S("S2_Far", 490, 50)
        ]
        self.routes = [
            Route("R1", [P(10,50), P(40,50), P(250,50)], ["S1_Far", "S1_Close", "T1"]),
            Route("R2", [P(250,50), P(460,50), P(490,50)], ["T1", "S2_Close", "S2_Far"])
        ]
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
