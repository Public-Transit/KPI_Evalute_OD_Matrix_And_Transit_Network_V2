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

class FakeRepoF5(AbstractRepository):
    """
    Filter Case 5: Comprehensive Mesh & Detour Transfer
    Một mạng lưới trạm liên hoàn và rất chồng chèo: 
    - Z1 (Tâm 50,50) có 3 trạm boarding. S1_Center là gần tâm nhất.
    - Z2 (Tâm 950,50) có 3 trạm alighting. S2_Center là gần tâm nhất.
    - Z_Hub (Tâm 500,50) nơi R1 và R2 gặp nhau với tận 3 trạm chung: T1, T2_Center, T3.
    - R1: Chạy từ Z1 tới HUB. Khi ở Z_Hub, R1 đi cực kỳ vòng vèo (lên T1 rồi vòng qua núi xa tít tắp mới tới T2_Center, T3).
    - R2: Chạy từ HUB tới Z2. Khi tiếp nhận khách ở Z_Hub tại các trạm T1, T2_Center, T3, R2 đều đi thẳng tắp về Z2 cực êm.
    MỤC TIÊU:
    Bộ lọc phải chọn Board_Stop = S1_Center, Alight_Stop = S2_Center, 
    NHƯNG Transfer_Stop phải chọn T1 dù nó T1, T2_Center hay T3 đều có thể transfer.
    Lý do: Xuống xe R1 tại T1 sớm nhất có thể sẽ tiết kiệm quãng đường vòng trên xe R1.
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
            S("S1f", 10, 50), S("S1m", 30, 50), S("S1c", 50, 50),
            S("T1", 450, 50), S("T2c", 500, 50), S("T3", 550, 50),
            S("S2c", 950, 50), S("S2m", 970, 50), S("S2f", 990, 50)
        ]
        self.routes = [
            # R1: Cực lằng nhằng ở nửa sau
            Route("R1", [
                P(10,50), P(30,50), P(50,50),        # Tới Z1 nhanh gọn
                P(450,50),                           # Tới T1
                P(450,500), P(500,500), P(500,50),   # Vòng một vòng qua bắc cực tới T2_Center
                P(500,-400), P(550,-400), P(550,50)  # Vòng qua nam cực tới T3
            ], ["S1f", "S1m", "S1c", "T1", "T2c", "T3"]),
            
            # R2: Rất thẳng thắn
            Route("R2", [
                P(450,50), P(500,50), P(550,50),     # Chạy qua T1, T2_Center, T3 không chớp mắt
                P(950,50), P(970,50), P(990,50)      # Giao tại Z2
            ], ["T1", "T2c", "T3", "S2c", "S2m", "S2f"])
        ]
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
