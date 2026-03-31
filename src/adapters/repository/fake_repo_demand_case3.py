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

class FakeRepoDemandCase3(AbstractRepository):
    """
    Case 3: Trip có 2 chặng (2 Legs) rẽ L-Shape. 
    Kèm theo một OD pair đi vào góc rẽ nhưng KHÔNG được chuyến đi tiếp.
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)
        def Z(zid, x, y): return Zone(zid, [P(x-10,y-10), P(x+10,y-10), P(x+10,y+10), P(x-10,y+10)], P(x,y))

        self.zones = [Z("ZA", 0, 100), Z("ZB", 100, 100), Z("ZC", 200, 100), Z("ZX", 100, 0), Z("ZY", 100, -100)]
        self.od_pairs = [
            ODPair("OD_A_C", "ZA", "ZC", 10), # Qua B (Leg1)-> Có phục vụ
            ODPair("OD_A_X", "ZA", "ZX", 0),  
            ODPair("OD_X_Y", "ZX", "ZY", 200), # Leg2 là B->X. Điểm X có được phục vụ. Có tính.
            ODPair("OD_C_X", "ZC", "ZX", 500), # Nằm trên các route R1, R2. Nhưng Trip chỉ qua Leg 1 (A-B) và Leg 2 (B-X). Không chứa đoạn mạn C hay X-Y.
        ]
        self.stops = [S("A", 0, 100), S("B", 100, 100), S("C", 200, 100), S("X", 100, 0), S("Y", 100, -100)]
        self.routes = [
            Route("R1", [P(0,100), P(100,100), P(200,100)], ["A", "B", "C"]),
            Route("R2", [P(100,100), P(100,0), P(100,-100)], ["B", "X", "Y"])
        ]
        # Trip rẽ L, Leg 1 đi A->B (nghỉ tại B). Leg 2 đổi tuyến R2 đi B->X. (Chưa qua C, chưa qua Y).
        self.trips = [Trip([Leg("R1", "A", "B"), Leg("R2", "B", "X")])]

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
