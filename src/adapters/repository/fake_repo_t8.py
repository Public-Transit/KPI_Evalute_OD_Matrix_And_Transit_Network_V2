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

class FakeRepoT8(AbstractRepository):
    """
    Test 8: Xử lý Lộ trình ứng viên hỗn hợp.
    Mục tiêu: Đưa vào tập dữ liệu chứa cả đi thẳng (0 transfer) và đi vòng (1 transfer).
    Hệ thống phải chốt ra đúng 1 lộ trình đại diện duy nhất tuân thủ hoàn hảo 2 mức độ ưu tiên.
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)

        self.zones = [
            Zone("Z1", [P(0,0), P(100,0), P(100,100), P(0,100)], P(50,50)),
            Zone("Z_Hub", [P(200,0), P(400,0), P(400,100), P(200,100)], P(300,50)),
            Zone("Z2", [P(500,0), P(600,0), P(600,100), P(500,100)], P(550,50))
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            # Tuyến trực tiếp (0 transfer): Đi bộ xa (20+20=40), nhưng không phải đổi xe
            S("S1_Direct", 70, 50), 
            S("S2_Direct", 530, 50),
            
            # Tuyến gom (Phần 1 của 1 transfer): Đi bộ gần (5), đổi xe tiện
            S("S1_Gom", 55, 50),
            S("T1", 300, 50),
            
            # Tuyến chính (Phần 2 của 1 transfer): Đi bộ về đích gần (5)
            S("S2_Express", 545, 50)
        ]
        self.routes = [
            # Route trực tiếp
            Route("R_Direct", [P(70,50), P(530,50)], ["S1_Direct", "S2_Direct"]),
            
            # Bundle 1-transfer
            Route("R1_Gom", [P(55,50), P(300,50)], ["S1_Gom", "T1"]),
            Route("R2_Exp", [P(300,50), P(545,50)], ["T1", "S2_Express"])
        ]
        # Kỳ vọng: Hệ thống chọn phương án 1-transfer vì nó có Walk Min (10) < Walk Min của direct (40).
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
