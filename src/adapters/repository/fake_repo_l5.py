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

class FakeRepoL5(AbstractRepository):
    """
    Level 5: Mạng lưới dệt kén (Web)
    """
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)

        self.zones = [
            Zone("Z1", [P(0,0), P(100,0), P(100,100), P(0,100)], P(50,50)),
            Zone("Z2", [P(600,600), P(700,600), P(700,700), P(600,700)], P(650,650)),
            Zone("Z3", [P(300,0), P(400,0), P(400,100), P(300,100)], P(350,50)),
            Zone("Z4", [P(0,300), P(100,300), P(100,400), P(0,400)], P(50,350)),
            Zone("Z5", [P(300,300), P(400,300), P(400,400), P(300,400)], P(350,350))
        ]
        self.od_pairs = [
            ODPair("OD_Z1_Z2", "Z1", "Z2", 1000), # Qua Z5 (R_Diag) hoặc ngoằn ngoèo qua Z3/Z4
            ODPair("OD_Z1_Z3", "Z1", "Z3", 200),  # Trực tiếp R_Horiz_Top
            ODPair("OD_Z1_Z4", "Z1", "Z4", 200),  # Trực tiếp R_Vert_Left
            ODPair("OD_Z1_Z5", "Z1", "Z5", 500),  # Trực tiếp R_Diag_Main
            ODPair("OD_Z3_Z5", "Z3", "Z5", 300),  # Trực tiếp R_Vert_Mid
            ODPair("OD_Z4_Z5", "Z4", "Z5", 300),  # Trực tiếp R_Horiz_Mid
            ODPair("OD_Z5_Z2", "Z5", "Z2", 800),  # Trực tiếp R_Diag_Main
            ODPair("OD_Z3_Z2", "Z3", "Z2", 400),  # Transfer tại Z5 hoặc tuyến chéo (nếu có bổ sung)
            ODPair("OD_Z4_Z2", "Z4", "Z2", 400)   # Transfer tại Z5 hoặc tuyến chéo (nếu có bổ sung)
        ]
        self.stops = [
            S("S1o", 50, 50), S("S2d", 650, 650),
            S("S3n", 350, 50), S("S4w", 50, 350), S("S5c", 350, 350),
            S("S6e", 650, 350), S("S7s", 350, 650)
        ]
        self.routes = [
            Route("Rht", [P(50,50), P(350,50)], ["S1o", "S3n"]),
            Route("Rvl", [P(50,50), P(50,350)], ["S1o", "S4w"]),
            Route("Rdm", [P(50,50), P(350,350), P(650,650)], ["S1o", "S5c", "S2d"]),
            Route("Rhm", [P(50,350), P(350,350), P(650,350)], ["S4w", "S5c", "S6e"]),
            Route("Rvm", [P(350,50), P(350,350), P(350,650)], ["S3n", "S5c", "S7s"]),
            Route("Rvr", [P(650,350), P(650,650)], ["S6e", "S2d"]),
            Route("Rhb", [P(350,650), P(650,650)], ["S7s", "S2d"])
        ]
        self.trips = []

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix: return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork: return TransitNetwork(self.stops, self.routes)
