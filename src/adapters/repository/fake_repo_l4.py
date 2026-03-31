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

class FakeRepoL4(AbstractRepository):
    """
    Level 4: Tranh chấp Thẳng vs Trung chuyển
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)

        self.zones = [
            Zone("Z1", [P(0,0), P(100,0), P(100,100), P(0,100)], P(50,50)),
            Zone("Z_Hub", [P(250,150), P(350,150), P(350,250), P(250,250)], P(300,200)),
            Zone("Z2", [P(500,0), P(600,0), P(600,100), P(500,100)], P(550,50))
        ]
        self.od_pairs = [
            ODPair("OD1", "Z1", "Z2", 100),       # Z1 -> Z2 (Thẳng R_ThangNhungVong vs Transfer qua Hub)
            ODPair("OD2", "Z1", "Z_Hub", 50),     # Z1 -> Hub (Direct R_Transfer_Feed)
            ODPair("OD3", "Z_Hub", "Z2", 50)      # Hub -> Z2 (Direct R_Transfer_Exp)
        ]
        self.stops = [
            S("S1z", 50, 50), 
            S("S2z", 550, 50), 
            S("H1", 300, 200),
            S("L1", 100,-200), 
            S("L2", 400,-200)
        ]
        self.routes = [
            Route("Rtv", [P(50,50), P(100,-200), P(400,-200), P(550,50)], ["S1z", "L1", "L2", "S2z"]),
            Route("Rtf", [P(50,50), P(300,200)], ["S1z", "H1"]),
            Route("Rte", [P(300,200), P(550,50)], ["H1", "S2z"])
        ]
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
