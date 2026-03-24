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
        # Mạng lưới 3x3 (mỗi cạnh 100m, tổng 300x300m)
        # 4 zones chia 4 ô vuông 150x150m
        self.zones = [
            Zone("Z1", [Point(0,0), Point(150,0), Point(150,150), Point(0,150)], Point(75,75)),
            Zone("Z2", [Point(150,0), Point(300,0), Point(300,150), Point(150,150)], Point(225,75)),
            Zone("Z3", [Point(0,150), Point(150,150), Point(150,300), Point(0,300)], Point(75,225)),
            Zone("Z4", [Point(150,150), Point(300,150), Point(300,300), Point(150,300)], Point(225,225))
        ]
        
        # 4 trường hợp OD Pair
        self.od_pairs = [
            ODPair("OD1", "Z1", "Z2", 100), # Trực tiếp
            ODPair("OD2", "Z1", "Z4", 100), # Chuyển 1 lần
            ODPair("OD3", "Z1", "Z3", 100), # Chuyển 2 lần
            ODPair("OD4", "Z3", "Z1", 100)  # Không có tuyến
        ]
        
        # Stops tại các mắt lưới (cách nhau 100m)
        self.stops = [
            Stop("S00", 0, 0), Stop("S10", 100, 0), Stop("S20", 200, 0), Stop("S30", 300, 0),
            Stop("S01", 0, 100), Stop("S11", 100, 100), Stop("S21", 200, 100), Stop("S31", 300, 100),
            Stop("S02", 0, 200), Stop("S12", 100, 200), Stop("S22", 200, 200), Stop("S32", 300, 200),
            Stop("S03", 0, 300), Stop("S13", 100, 300), Stop("S23", 200, 300), Stop("S33", 300, 300)
        ]
        
        # 5 tuyến xe buýt
        self.routes = [
            # R1 đi ngang từ trái sang phải, qua Z1 và Z2
            Route("R1", [Point(0,100), Point(100,100), Point(200,100), Point(300,100)], ["S01", "S11", "S21", "S31"]),
            # R2 đi dọc từ dưới lên trên, qua Z2 và Z4
            Route("R2", [Point(200,0), Point(200,100), Point(200,200), Point(200,300)], ["S20", "S21", "S22", "S23"]),
            # R3 đi ngang từ phải sang trái, qua Z4 và Z3
            Route("R3", [Point(300,200), Point(200,200), Point(100,200), Point(0,200)], ["S32", "S22", "S12", "S02"]),
            # R4 đi nội bộ trong Z3
            Route("R4", [Point(0,200), Point(0,300), Point(100,300)], ["S02", "S03", "S13"]),
            # R5 đi nội bộ trong Z2
            Route("R5", [Point(200,0), Point(300,0), Point(300,100)], ["S20", "S30", "S31"])
        ]
        
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
        
    def get_od_matrix(self) -> ODMatrix:
        return ODMatrix(self.od_pairs, self.zones)
        
    def get_transit_network(self) -> TransitNetwork:
        return TransitNetwork(self.stops, self.routes)