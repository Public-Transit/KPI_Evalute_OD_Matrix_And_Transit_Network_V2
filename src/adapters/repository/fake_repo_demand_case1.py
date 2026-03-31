from typing import Tuple
from src.domain.model.point import Point
from src.domain.model.stop import Stop
from src.domain.model.route import Route
from src.domain.model.zone import Zone
from src.domain.model.od_pair import ODPair
from src.domain.model.leg import Leg
from src.domain.model.trip import Trip
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.adapters.repository.abstract_repository import AbstractRepository

class FakeRepoDemandCase1(AbstractRepository):
    """
    Case 1: Trip có 1 chặng (1 Leg) trên 1 tuyến thẳng.
    Có chứa OD được phục vụ bởi Route nhưng KHÔNG được phục vụ bởi Trip.
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)
        def Z(zid, x, y): return Zone(zid, [P(x-10,y-10), P(x+10,y-10), P(x+10,y+10), P(x-10,y+10)], P(x,y))

        self.zones = [Z("ZA", 0, 50), Z("ZB", 100, 50), Z("ZC", 200, 50), Z("ZD", 300, 50), Z("ZE", 400, 50)]
        self.od_pairs = [
            ODPair("OD_A_E", "ZA", "ZE", 10), # Qua B-C -> Phục vụ
            ODPair("OD_B_C", "ZB", "ZC", 20), # Trùng B-C -> Phục vụ
            ODPair("OD_D_E", "ZD", "ZE", 100) # Cuối tuyến R1, nhưng Trip chỉ đi B-C -> KHÔNG Phục vụ
        ]
        self.stops = [S("A", 0, 50), S("B", 100, 50), S("C", 200, 50), S("D", 300, 50), S("E", 400, 50)]
        self.routes = [
            Route("R1", [P(0,50), P(100,50), P(200,50), P(300,50), P(400,50)], ["A", "B", "C", "D", "E"])
        ]
        self.trips = [Trip([Leg("R1", "B", "C")])]

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
