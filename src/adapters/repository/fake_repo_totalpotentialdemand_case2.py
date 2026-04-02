from typing import Tuple
from src.domain.model.point import Point
from src.domain.model.stop import Stop
from src.domain.model.route import Route
from src.domain.model.zone import Zone
from src.domain.model.od_pair import ODPair
from src.domain.model.trip import Trip
from src.domain.model.leg import Leg
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.adapters.repository.abstract_repository import AbstractRepository

class FakeRepoTotalPotentialDemandCase2(AbstractRepository):
    def __init__(self):
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)
        
        self.zones = []
        self.stops = []
        self.routes = []
        self.od_pairs = []
        self.trips = []      
        self.candidate_trips_for_vis = [["S3", "S4", "S5", "S6", "S7"]] 
        
        for i in range(1, 11):
            self.stops.append(S(f"S{i}", (i-1)*100, 100))
        self.stops.extend([
            S("S11", 400, 500), S("S12", 400, 400), S("S13", 400, 300), S("S14", 400, 200),
            S("S15", 400, 0), S("S16", 400, -100), S("S17", 400, -200), S("S18", 400, -300)
        ])
        self.stops.extend([
            S("S21", 700, 500), S("S22", 700, 400), S("S23", 700, 300), S("S24", 700, 200),
            S("S25", 700, 0), S("S26", 700, -100), S("S27", 700, -200), S("S28", 700, -300)
        ])
        
        r1_stops = [f"S{i}" for i in range(1, 11)]
        r2_stops = ["S11", "S12", "S13", "S14", "S5", "S15", "S16", "S17", "S18"]
        r3_stops = ["S21", "S22", "S23", "S24", "S8", "S25", "S26", "S27", "S28"]
        
        def to_shape(sids): return [s.coord() for sid in sids for s in self.stops if s.id() == sid]
        self.routes.append(Route("R1", to_shape(r1_stops), r1_stops))
        self.routes.append(Route("R2", to_shape(r2_stops), r2_stops))
        self.routes.append(Route("R3", to_shape(r3_stops), r3_stops))
        
        def make_zone(zid, cx, cy):
            self.zones.append(Zone(zid, [P(cx-50, cy-50), P(cx+150, cy-50), P(cx+150, cy+50), P(cx-50, cy+50)], P(cx+50, cy)))
        make_zone("Z1", 0, 100); make_zone("Z2", 200, 100); make_zone("Z3", 500, 100); make_zone("Z4", 800, 100)
        make_zone("Z5", 400, 400); make_zone("Z6", 400, -200); make_zone("Z7", 700, 400); make_zone("Z8", 700, -200)

        # CASE 2 SPECIFIC
        self.od_pairs.append(ODPair("OD_2_3", "Z2", "Z3", 100.0))
        self.trips = [
            Trip([Leg("R1", "S5", "S9")]),
            Trip([Leg("R2", "S12", "S5"), Leg("R1", "S5", "S10")])
        ]

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips
    def get_od_matrix(self) -> ODMatrix:
        return ODMatrix(self.od_pairs, self.zones)
    def get_transit_network(self) -> TransitNetwork:
        return TransitNetwork(self.stops, self.routes)
