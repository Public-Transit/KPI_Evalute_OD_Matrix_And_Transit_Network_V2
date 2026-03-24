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

class FakeRepository(AbstractRepository):
    def __init__(self):
        # Biến đổi toạ độ Cartesian (m) sang Lat/Lon (100m ~ 0.001 degree)
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)

        # Mạng lưới 3x3 (mỗi cạnh 100m, tổng 300x300m)
        self.zones = [
            Zone("Z1", [P(0,0), P(150,0), P(150,150), P(0,150)], P(75,75)),
            Zone("Z2", [P(150,0), P(300,0), P(300,150), P(150,150)], P(225,75)),
            Zone("Z3", [P(0,150), P(150,150), P(150,300), P(0,300)], P(75,225)),
            Zone("Z4", [P(150,150), P(300,150), P(300,300), P(150,300)], P(225,225))
        ]
        
        # Tạo ra 12 cặp OD (6 chiều đi, 6 chiều về) liên kết tất cả 4 vùng
        self.od_pairs = [
            # Chiều đi
            ODPair("OD1", "Z1", "Z2", 100), # Trực tiếp (R1)
            ODPair("OD2", "Z1", "Z4", 100), # Chuyển 1 lần (R1 -> R2)
            ODPair("OD3", "Z1", "Z3", 100), # Chuyển 2 lần (R1 -> R2 -> R3)
            ODPair("OD4", "Z2", "Z3", 100), # Chuyển 1 lần (R2 -> R3)
            ODPair("OD5", "Z2", "Z4", 100), # Trực tiếp (R2)
            ODPair("OD6", "Z3", "Z4", 100), # Không có tuyến / Ngược chiều R3
            
            # 6 OD ngược chiều lại
            ODPair("OD7", "Z2", "Z1", 100), # Ngược chiều R1
            ODPair("OD8", "Z4", "Z1", 100), # Ngược chiều R2 -> R1
            ODPair("OD9", "Z3", "Z1", 100), # Ngược chiều R3 -> R2 -> R1
            ODPair("OD10", "Z3", "Z2", 100), # Ngược chiều R3 -> R2
            ODPair("OD11", "Z4", "Z2", 100), # Ngược chiều R2
            ODPair("OD12", "Z4", "Z3", 100), # Trực tiếp chiều ngược (R3)
        ]
        
        # Stops tại các mắt lưới (cách nhau 100m)
        self.stops = [
            S("S00", 0, 0), S("S10", 100, 0), S("S20", 200, 0), S("S30", 300, 0),
            S("S01", 0, 100), S("S11", 100, 100), S("S21", 200, 100), S("S31", 300, 100),
            S("S02", 0, 200), S("S12", 100, 200), S("S22", 200, 200), S("S32", 300, 200),
            S("S03", 0, 300), S("S13", 100, 300), S("S23", 200, 300), S("S33", 300, 300)
        ]
        
        # 5 tuyến xe buýt
        self.routes = [
            Route("R1", [P(0,100), P(100,100), P(200,100), P(300,100)], ["S01", "S11", "S21", "S31"]),
            Route("R2", [P(200,0), P(200,100), P(200,200), P(200,300)], ["S20", "S21", "S22", "S23"]),
            Route("R3", [P(300,200), P(200,200), P(100,200), P(0,200)], ["S32", "S22", "S12", "S02"]),
            Route("R4", [P(0,200), P(0,300), P(100,300)], ["S02", "S03", "S13"]),
            Route("R5", [P(200,0), P(300,0), P(300,100)], ["S20", "S30", "S31"])
        ]
        
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
        
    def get_od_matrix(self) -> ODMatrix:
        return ODMatrix(self.od_pairs, self.zones)
        
    def get_transit_network(self) -> TransitNetwork:
        return TransitNetwork(self.stops, self.routes)