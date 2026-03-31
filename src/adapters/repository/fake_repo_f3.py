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

class FakeRepoF3(AbstractRepository):
    """
    Filter Case 3: Transfer Optimization
    Đường chuyển tuyến có ngã ba xa. Chọn luồng chuyển tiếp có quãng đường di chuyển chung ngắn nhất.
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
            S("S1", 50, 50), S("S2", 450, 50),
            S("T1", 210, 50), S("T2", 290, 50), 
            S("M_Detour", 250, 200) # Điểm vòng vèo trên tuyến R1 ở Hub
        ]
        self.routes = [
            Route("R1", [P(50,50), P(210,50), P(250,200), P(290,50)], ["S1", "T1", "M_Detour", "T2"]),
            Route("R2", [P(210,50), P(290,50), P(450,50)], ["T1", "T2", "S2"])
        ]
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
