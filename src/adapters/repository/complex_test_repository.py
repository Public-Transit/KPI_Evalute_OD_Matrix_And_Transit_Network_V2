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

class ComplexTestRepository(AbstractRepository):
    def __init__(self):
        # Biến đổi toạ độ Cartesian (m) sang Lat/Lon (100m ~ 0.001 degree)
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)

        # 1. Các Vùng
        self.zones = [
            Zone("Z0", [P(0,0), P(100,0), P(100,100), P(0,100)], P(50,50)),
            Zone("Z1", [P(1000,0), P(1100,0), P(1100,100), P(1000,100)], P(1050,50)),
            Zone("ZT", [P(500,0), P(600,0), P(600,100), P(500,100)], P(550,50))
        ]
        
        # 2. Các cặp OD
        self.od_pairs = [
            ODPair("OD_Complex", "Z0", "Z1", 1000)
        ]
        
        # 3. Các Trạm
        self.stops = [
            # Khu vực Z0 (Origin)
            S("S0_1", 50, 50),   # Tối ưu nhất cho Z0
            S("S0_2", 40, 40),   # Kém hơn
            
            # Khu vực Z1 (Destination)
            S("S1_1", 1050, 50), # Tối ưu nhất cho Z1
            S("S1_2", 1060, 60), # Kém hơn
            
            # Khu vực ZT (Transfer)
            S("ST_1", 550, 50),  # Điểm chuyển tiếp 1
            S("ST_2", 540, 40),  # Điểm chuyển tiếp 2
            
            # Trạm trung gian (để tạo độ dài cho TieBreak)
            S("SM_1", 300, 200),
            S("SM_2", 800, -100)
        ]
        
        # 4. Các Tuyến
        self.routes = [
            # 3 Tuyến đi thẳng:
            # R_Direct_Best: Đường thẳng, trạm tối ưu
            Route("R_Best", [P(50,50), P(1050,50)], ["S0_1", "S1_1"]),
            
            # R_Direct_TieBreak: Trạm tối ưu nhưng đường đi vòng vèo (dài hơn)
            Route("R_TieBreak", [P(50,50), P(300,200), P(800,-100), P(1050,50)], ["S0_1", "SM_1", "SM_2", "S1_1"]),
            
            # R_Direct_Far: Trạm xa tâm zone hơn
            Route("R_Far", [P(40,40), P(1060,60)], ["S0_2", "S1_2"]),
            
            # 2 Kịch bản trung chuyển (Tổng 4 tuyến):
            # Transfer 1 (Via ST_1) - R_Feed1 và R_Exp1
            Route("R_Feed1", [P(50,50), P(550,50)], ["S0_1", "ST_1"]),
            Route("R_Exp1", [P(550,50), P(1050,50)], ["ST_1", "S1_1"]),
            
            # Transfer 2 (Via ST_2) - R_Feed2 và R_Exp2
            Route("R_Feed2", [P(40,40), P(540,40)], ["S0_2", "ST_2"]),
            Route("R_Exp2", [P(540,40), P(1060,60)], ["ST_2", "S1_2"])
        ]
        
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
        
    def get_od_matrix(self) -> ODMatrix:
        return ODMatrix(self.od_pairs, self.zones)
        
    def get_transit_network(self) -> TransitNetwork:
        return TransitNetwork(self.stops, self.routes)
