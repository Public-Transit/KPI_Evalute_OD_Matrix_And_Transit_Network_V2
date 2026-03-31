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

class FakeRepoT2(AbstractRepository):
    """
    Transfer Case 2: Tuyến 1-transfer.
    Z1 và Z2 không kết nối trực tiếp. Phải quá cảnh tại Z3 (Hub).
    Số lần chuyển tuyến kỳ vọng = 1.
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)

        self.zones = [
            Zone("Z1", [P(-10,-10), P(10,-10), P(10,10), P(-10,10)], P(0,0)),
            Zone("Z_Hub", [P(40,-10), P(60,-10), P(60,10), P(40,10)], P(50,0)),
            Zone("Z2", [P(90,-10), P(110,-10), P(110,10), P(90,10)], P(100,0))
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            S("S1_Start", 0, 0),
            S("S_Transfer_Hub", 50, 0),
            S("S2_End", 100, 0)
        ]
        self.routes = [
            Route("R1_First_Leg", [P(0,0), P(50,0)], ["S1_Start", "S_Transfer_Hub"]),
            Route("R2_Second_Leg", [P(50,0), P(100,0)], ["S_Transfer_Hub", "S2_End"])
        ]
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
