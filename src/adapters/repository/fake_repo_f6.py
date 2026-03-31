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

class FakeRepoF6(AbstractRepository):
    """
    Filter Case 6: O/D Symmetry Tie-Breaker for 1-Transfer.
    Test việc giải quyết trường hợp hòa (equal access distance) ở điểm đầu cuối bằng cách chọn
    cặp Boarding/Alighting giúp tổng quãng đường di chuyển trên xe (route distance) là ngắn nhất.
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)

        self.zones = [
            # Z1 tâm ở (50, 50)
            Zone("Z1", [P(0,0), P(100,0), P(100,100), P(0,100)], P(50,50)),
            Zone("Z_Hub", [P(200,0), P(300,0), P(300,100), P(200,100)], P(250,50)),
            # Z2 tâm ở (450, 50)
            Zone("Z2", [P(400,0), P(500,0), P(500,100), P(400,100)], P(450,50))
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            # Boarding: S1_Top và S1_Bot cách tâm (50,50) đều bằng 10. Nhưng S1_Bot thuận lộ trình hơn.
            S("S1_Top_Tie", 50, 60), 
            S("S1_Bot_Tie", 50, 40), 
            S("T1", 250, 50),
            # Alighting: S2_Top và S2_Bot cách tâm (450,50) đều bằng 10. S2_Top thuận lộ trình hơn.
            S("S2_Top_Tie", 450, 60),
            S("S2_Bot_Tie", 450, 40)
        ]
        self.routes = [
            # Tuyến 1 đi dích dắc S1_Top -> S1_Bot -> Hub.
            # Rõ ràng lên ở S1_Bot sẽ bớt được quãng xe chạy (50,60) -> (50,40)
            Route("R1", [P(50,60), P(50,40), P(250,50)], ["S1_Top_Tie", "S1_Bot_Tie", "T1"]),
            
            # Tuyến 2 đi từ Hub -> S2_Top -> S2_Bot.
            # Xuống ở S2_Top sẽ xuống xe sớm hơn.
            Route("R2", [P(250,50), P(450,60), P(450,40)], ["T1", "S2_Top_Tie", "S2_Bot_Tie"])
        ]
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
