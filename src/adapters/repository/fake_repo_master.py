from typing import Tuple
import math
from src.domain.model.point import Point
from src.domain.model.stop import Stop
from src.domain.model.route import Route
from src.domain.model.zone import Zone
from src.domain.model.od_pair import ODPair
from src.domain.model.trip import Trip
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.adapters.repository.abstract_repository import AbstractRepository

class FakeRepoMaster(AbstractRepository):
    """
    Master Case: Mô phỏng mạng lưới thực tế của một thành phố quy mô nhỏ.
    - 15 Vùng (Z1 - Z15).
    - 10 Tuyến (R1 - R10) bao gồm Tuyến trục (Trunk), Tuyến gom (Feeder) và Tuyến vòng (Circular).
    - Hơn 50 trạm dừng.
    - Nhiều cặp OD kiểm thử các tổ hợp Routing + Filtering khác nhau.
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/10000.0, 105.0 + y/10000.0) # Scale lớn hơn 10 lần
        def S(sid, x, y): return Stop(sid, 21.0 + x/10000.0, 105.0 + y/10000.0)

        # 1. Tạo 15 Zone (Bố cục lưới 3x5)
        self.zones = []
        for i in range(3):
            for j in range(5):
                zid = f"Z{i*5 + j + 1}"
                x, y = j*200, i*200
                boundary = [P(x,y), P(x+150,y), P(x+150,y+150), P(x,y+150)]
                centroid = P(x+75, y+75)
                self.zones.append(Zone(zid, boundary, centroid))

        # 2. Tạo Trạm dừng (Rải rác trên các trục chính)
        self.stops = []
        stop_counter = 1
        
        # Tạo trạm và lưu vết để gán vào Route sau
        h_stops = {} # row -> list of stop_ids
        v_stops = {} # col -> list of stop_ids

        # Trục ngang X=100, 300, 500, 700, 900 cho Y=75, 275, 475
        for row in [75, 275, 475]:
            h_stops[row] = []
            for col in range(50, 1000, 50):
                sid = f"#{stop_counter}"
                self.stops.append(Stop(sid, 21.0 + col/10000.0, 105.0 + row/10000.0))
                h_stops[row].append(sid)
                stop_counter += 1

        # Trục dọc Y=100, 300, 500 cho X=75, 275, 475, 675, 875
        for col in [75, 275, 475, 675, 875]:
            v_stops[col] = []
            for row in range(50, 600, 50):
                # Kiểm tra xem có trạm nào ở vị trí này chưa (trùng giao điểm)
                existing = [s for s in self.stops if abs(s.coord().lat() - (21.0 + col/10000.0)) < 1e-7 
                            and abs(s.coord().lon() - (105.0 + row/10000.0)) < 1e-7]
                if existing:
                    sid = existing[0].id()
                else:
                    sid = f"#{stop_counter}"
                    self.stops.append(Stop(sid, 21.0 + col/10000.0, 105.0 + row/10000.0))
                    stop_counter += 1
                v_stops[col].append(sid)

        # 3. Tạo 10 Tuyến xe buýt
        self.routes = []
        
        # R1, R2: Tuyến trục ngang (Express/Trunk)
        self.routes.append(Route("R1_Main_H", [P(50, 75), P(950, 75)], h_stops[75]))
        self.routes.append(Route("R2_Main_H", [P(50, 275), P(950, 275)], h_stops[275]))
        
        # R3, R4: Tuyến trục dọc (Trunk)
        self.routes.append(Route("R3_Main_V", [P(75, 50), P(75, 550)], v_stops[75]))
        self.routes.append(Route("R4_Main_V", [P(475, 50), P(475, 550)], v_stops[475]))

        # R5, R6: Tuyến gom (Feeder) - Vòng vèo (Chọn tay vài trạm để test)
        # R5 nối từ Z1 góc trái dưới lên tâm
        f5_stops = [h_stops[75][0], v_stops[75][1], v_stops[275][2], h_stops[275][5]]
        self.routes.append(Route("R5_Feeder", [P(50,75), P(75,100), P(275,150), P(300,275)], f5_stops))
        
        # R7: Tuyến vòng (Circular) trung tâm
        # Lấy các trạm quanh vùng tâm X=400..500, Y=200..300
        circular_stops = [h_stops[275][7], h_stops[275][9], v_stops[475][5], v_stops[475][3], h_stops[275][7]]
        self.routes.append(Route("R7_Circular", [P(400,275), P(500,275), P(475,300), P(475,200), P(400,275)], circular_stops))

        # R8: Diag
        self.routes.append(Route("R8_Diag", [P(50,50), P(950,550)], [h_stops[75][1], v_stops[475][5], v_stops[875][9]]))
        self.routes.append(Route("R9_Short", [P(675,50), P(675,200)], v_stops[675][:3]))
        self.routes.append(Route("R10_Connect", [P(475,475), P(875,475)], [v_stops[475][9], h_stops[475][9], v_stops[875][9]]))

        # 4. Các cặp OD kiểm thử
        self.od_pairs = [
            ODPair("OD_Master_1", "Z1", "Z15", 1000),  # Xuyên góc thành phố
            ODPair("OD_Master_2", "Z1", "Z3", 500),    # Đi ngang
            ODPair("OD_Master_3", "Z6", "Z10", 300),   # Tuyến gom
            ODPair("OD_Master_4", "Z8", "Z13", 200),   # Trung chuyển trung tâm
            ODPair("OD_Master_5", "Z1", "Z2", 100),    # Vùng lân cận
        ]
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
