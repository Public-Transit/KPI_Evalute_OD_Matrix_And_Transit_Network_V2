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

class FakeRepoDemandCase4(AbstractRepository):
    """
    Case 4: Trip có 2 chặng, ngắt quãng ở giữa (Đoạn giữa khách muốn lên thì không có Leg).
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)
        def Z(zid, x, y): return Zone(zid, [P(x-10,y-10), P(x+10,y-10), P(x+10,y+10), P(x-10,y+10)], P(x,y))

        self.zones = [Z("ZA", 0, 100), Z("ZB", 100, 100), Z("ZC", 200, 100), Z("ZD", 300, 100), Z("ZE", 400, 100), Z("ZF", 500, 100)]
        self.od_pairs = [
            ODPair("OD_A_F", "ZA", "ZF", 100), # Trùm cả 2 Leg, có tính
            ODPair("OD_C_D", "ZC", "ZD", 400), # Nằm lọt thỏm ở giữa đoạn C->D. Leg 1 là A->B, Leg 2 là E->F. KHÔNG chạm bất kỳ trạm nào của Trip -> KHÔNG tính!
            ODPair("OD_E_F", "ZE", "ZF", 10)   # Trùng Leg 2, có tính.
        ]
        self.stops = [S("A", 0, 100), S("B", 100, 100), S("C", 200, 100), S("D", 300, 100), S("E", 400, 100), S("F", 500, 100)]
        self.routes = [
            Route("R1", [P(0,100), P(100,100), P(200,100), P(300,100), P(400,100), P(500,100)], ["A", "B", "C", "D", "E", "F"])
        ]
        # Trip đi từ A->B. Sau đó do phân ca trực,... xe tắt định vị, qua E, rỗng đến F.
        self.trips = [Trip([Leg("R1", "A", "B"), Leg("R1", "E", "F")])]

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
