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

class FakeRepoT6(AbstractRepository):
    """
    Test 6: Xử lý trùng khoảng cách đi bộ (1 chuyển tuyến).
    Mục tiêu: Khi nhiều phương án có chung Walking Min, chọn phương án có tổng xé buýt Min.
    (Giống Test 2 nhưng mức độ phức tạp cao hơn).
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)

        self.zones = [
            Zone("Z1", [P(0,0), P(100,0), P(100,100), P(0,100)], P(50,50)),
            Zone("Z_Hub", [P(300,0), P(500,0), P(500,100), P(300,100)], P(400,50)),
            Zone("Z2", [P(700,0), P(800,0), P(800,100), P(700,100)], P(750,50))
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            # Hai bến đều cách tâm Z1 đoạn 5 đơn vị
            S("S1_Top", 50, 55), 
            S("S1_Bot", 50, 45), 
            
            # Hub
            S("T1", 400, 50),
            
            # Hai bến đều cách tâm Z2 đoạn 5 đơn vị
            S("S2_Top", 750, 55),
            S("S2_Bot", 750, 45)
        ]
        self.routes = [
            # Tuyến 1: Đi vòng hơn
            Route("R_L1", [P(50,55), P(50,155), P(400,50)], ["S1_Top", "T1"]),
            # Tuyến 2: Đi thẳng hơn
            Route("R_L2", [P(50,45), P(400,50)], ["S1_Bot", "T1"]),
            
            # Tuyến 3: Đi vòng hơn
            Route("R_L3", [P(400,50), P(750,155), P(750,55)], ["T1", "S2_Top"]),
            # Tuyến 4: Đi thẳng hơn
            Route("R_L4", [P(400,50), P(750,45)], ["T1", "S2_Bot"])
        ]
        # Kết quả mong muốn: S1_Bot -> T1 -> S2_Bot (Best bus distance)
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
