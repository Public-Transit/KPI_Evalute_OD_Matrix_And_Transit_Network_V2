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

class FakeRepoDemandCase2(AbstractRepository):
    """
    Case 2: Trip có 1 chặng (1 Leg) trên mạng lưới đa tuyến (nhánh cây).
    Có chứa OD được phục vụ bởi Route nhưng KHÔNG được phục vụ bởi Trip.
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)
        def Z(zid, x, y): return Zone(zid, [P(x-10,y-10), P(x+10,y-10), P(x+10,y+10), P(x-10,y+10)], P(x,y))

        self.zones = [Z("ZA", 0, 100), Z("ZB", 100, 100), Z("ZC", 200, 100), Z("ZX", 200, 200)]
        self.od_pairs = [
            ODPair("OD_A_C", "ZA", "ZC", 50), # Trên R1, trùm lên Trip A-B -> Phục vụ
            ODPair("OD_B_X", "ZB", "ZX", 60), # Trên R2, nhưng Trip là R1! -> KHÔNG phục vụ bởi Trip, dù đi qua nút B. Trip ko rẽ về X. 
            ODPair("OD_A_X", "ZA", "ZX", 0)  # Thử nghiệm OD rẽ nhánh
        ]
        self.stops = [S("A", 0, 100), S("B", 100, 100), S("C", 200, 100), S("X", 200, 200)]
        self.routes = [
            Route("R1", [P(0,100), P(100,100), P(200,100)], ["A", "B", "C"]),
            Route("R2", [P(0,100), P(100,100), P(200,200)], ["A", "B", "X"])
        ]
        # Trip rẽ theo nhánh C, chỉ đi A -> B. 
        self.trips = [Trip([Leg("R1", "A", "B")])]

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
