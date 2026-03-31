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

class FakeRepoT3(AbstractRepository):
    """
    Test 3: Ưu tiên khoảng cách tiếp cận (Walking) hơn khoảng cách di chuyển bus (Direct).
    Mục tiêu: Kiểm tra sự xung đột giữa 2 ưu tiên. Hệ thống phải chọn Route có Walking Min.
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)

        self.zones = [
            Zone("Z1", [P(0,0), P(100,0), P(100,100), P(0,100)], P(50,50)),
            Zone("Z2", [P(300,0), P(400,0), P(400,100), P(300,100)], P(350,50))
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            # Tuyến A: Đi bộ Min (5+5=10), Bus dài (290)
            S("S1_WalkMin_O", 55, 50), 
            S("S2_WalkMin_D", 345, 50),
            # Tuyến B: Đi bộ lớn (20+20=40), Bus ngắn (260)
            S("S3_BusMin_O", 70, 50),
            S("S4_BusMin_D", 330, 50)
        ]
        self.routes = [
            Route("R_WalkMin", [P(55,50), P(345,50)], ["S1_WalkMin_O", "S2_WalkMin_D"]),
            Route("R_BusMin", [P(70,50), P(330,50)], ["S3_BusMin_O", "S4_BusMin_D"])
        ]
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
