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

class FakeRepoT5(AbstractRepository):
    """
    Test 5: Tối ưu toàn diện (Tiếp cận Min + Trung chuyển Min).
    Mục tiêu: Tìm được lộ trình có tổng đi bộ là Min, đồng thời điểm trung chuyển giúp bus distance là Min.
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)

        self.zones = [
            Zone("Z1", [P(0,0), P(100,0), P(100,100), P(0,100)], P(50,50)),
            Zone("Z_Hub", [P(400,0), P(600,0), P(600,100), P(400,100)], P(500,50)),
            Zone("Z2", [P(900,0), P(1000,0), P(1000,100), P(900,100)], P(950,50))
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            S("S1_O", 55, 50),   # Walk at O = 5
            S("S2_D", 945, 50),  # Walk at D = 5
            
            # Các bến trung chuyển tại Hub
            S("T_Short", 500, 50), # Nằm thẳng hàng Path O-D
            S("T_Long", 500, 200),  # Nằm lệch (Detour)
            S("T_Longer", 500, 400) # Nằm lệch xa hơn
        ]
        self.routes = [
            # Tuyến gom (Feeder) từ O đến Hub qua các bến khác nhau
            Route("R_Feeder", [P(55,50), P(500,50), P(500,200), P(500,400)], 
                  ["S1_O", "T_Short", "T_Long", "T_Longer"]),
            
            # Tuyến trục (Express) từ Hub đến D qua các bến
            Route("R_Express", [P(500,400), P(500,200), P(500,50), P(945,50)], 
                  ["T_Longer", "T_Long", "T_Short", "S2_D"])
        ]
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
