import random
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

class FakeRepoGrid3x3(AbstractRepository):
    def __init__(self, seed=42):
        random.seed(seed)
        
        # Helper: x,y in meters -> Lat/Lon
        def P(x, y): return Point(21.0 + x/100000.0, 105.0 + y/100000.0)
        def S(sid, x, y): return Stop(sid, 21.0 + x/100000.0, 105.0 + y/100000.0)
        
        self.zones = []
        self.stops = []
        self.routes = []
        self.od_pairs = []
        self.trips = []
        
        stops_by_zone = {}
        hubs = {}
        
        # 1. Generate Zones and Stops
        stop_id_counter = 1
        for i in range(3): # y (0=bottom, 1=mid, 2=top)
            for j in range(3): # x (0=left, 1=mid, 2=right)
                z_idx = i*3 + j + 1
                z_id = f"Z{z_idx}"
                
                x0, y0 = j * 300, i * 300
                x1, y1 = x0 + 300, y0 + 300
                cx, cy = x0 + 150, y0 + 150
                
                # Zone boundary
                pts = [P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)]
                self.zones.append(Zone(z_id, pts, P(cx, cy)))
                
                # Hub stop (center)
                hub = S(f"H{z_idx}", cx, cy)
                hubs[z_id] = hub
                self.stops.append(hub)
                
                # Random stops
                zone_stops = []
                n_stops = random.randint(4, 7)
                for _ in range(n_stops):
                    sx = random.randint(x0 + 30, x1 - 30)
                    sy = random.randint(y0 + 30, y1 - 30)
                    # avoid too close to hub
                    if abs(sx - cx) < 20 and abs(sy - cy) < 20:
                        sx += 30
                    
                    s = S(f"s{stop_id_counter}", sx, sy)
                    zone_stops.append(s)
                    self.stops.append(s)
                    stop_id_counter += 1
                    
                stops_by_zone[z_id] = zone_stops

        def pick_and_sort(z_id, sort_by, n=2):
            lst = random.sample(stops_by_zone[z_id], min(n, len(stops_by_zone[z_id])))
            if sort_by == 'x': lst.sort(key=lambda s: s.coord().lat())
            elif sort_by == '-x': lst.sort(key=lambda s: s.coord().lat(), reverse=True)
            elif sort_by == 'y': lst.sort(key=lambda s: s.coord().lon())
            elif sort_by == '-y': lst.sort(key=lambda s: s.coord().lon(), reverse=True)
            elif sort_by == 'xy': lst.sort(key=lambda s: s.coord().lat() + s.coord().lon())
            elif sort_by == '-xy': lst.sort(key=lambda s: s.coord().lat() + s.coord().lon(), reverse=True)
            return lst

        # 2. Generate Routes
        # Route 1: Z7 -> Z4 -> Z1 -> Z2 -> Z5 -> Z8 (U-shape)
        r1_stops = []
        for zd, order in [("Z7", "-y"), ("Z4", "-y"), ("Z1", "x"), ("Z2", "y"), ("Z5", "y"), ("Z8", "y")]:
            pre = pick_and_sort(zd, order, 1)
            post = pick_and_sort(zd, order, 1)
            r1_stops.extend([pre[0], hubs[zd], post[0]])
        r1_shape = [s.coord() for s in r1_stops]
        self.routes.append(Route("R1", r1_shape, [s.id() for s in r1_stops]))

        # Route 2: Z7 -> Z8 -> Z5 -> Z6 -> Z3 -> Z2 (Zig-zag)
        r2_stops = []
        for zd, order in [("Z7", "x"), ("Z8", "-y"), ("Z5", "x"), ("Z6", "-y"), ("Z3", "-x"), ("Z2", "-x")]:
            pre = pick_and_sort(zd, order, 1)
            post = pick_and_sort(zd, order, 1)
            r2_stops.extend([pre[0], hubs[zd], post[0]])
        r2_shape = [s.coord() for s in r2_stops]
        self.routes.append(Route("R2", r2_shape, [s.id() for s in r2_stops]))

        # Route 3: Z1 -> Z5 -> Z9 (Diagonal)
        r3_stops = []
        for zd, order in [("Z1", "xy"), ("Z5", "xy"), ("Z9", "xy")]:
            pre = pick_and_sort(zd, order, 2)
            post = pick_and_sort(zd, order, 2)
            r3_stops.extend([pre[0], pre[1], hubs[zd], post[0], post[1]])
        r3_shape = [s.coord() for s in r3_stops]
        self.routes.append(Route("R3", r3_shape, [s.id() for s in r3_stops]))

        # Route 4: Z9 -> Z6 -> Z3 (Vertical Right)
        r4_stops = []
        for zd, order in [("Z9", "-y"), ("Z6", "-y"), ("Z3", "-y")]:
            pre = pick_and_sort(zd, order, 2)
            post = pick_and_sort(zd, order, 2)
            r4_stops.extend([pre[0], pre[1], hubs[zd], post[0], post[1]])
        r4_shape = [s.coord() for s in r4_stops]
        self.routes.append(Route("R4", r4_shape, [s.id() for s in r4_stops]))

        # Route 5: Z4 -> Z5 -> Z6 (Horizontal Mid)
        r5_stops = []
        for zd, order in [("Z4", "x"), ("Z5", "x"), ("Z6", "x")]:
            pre = pick_and_sort(zd, order, 2)
            post = pick_and_sort(zd, order, 2)
            r5_stops.extend([pre[0], pre[1], hubs[zd], post[0], post[1]])
        r5_shape = [s.coord() for s in r5_stops]
        self.routes.append(Route("R5", r5_shape, [s.id() for s in r5_stops]))

        # 3. Generate OD Pairs with distinct demand flows
        self.od_pairs = [
            ODPair("OD_4_6", "Z4", "Z6", 450.0), # Direct R5 (Heavy)
            ODPair("OD_7_8", "Z7", "Z8", 120.0), # Direct R2
            ODPair("OD_7_9", "Z7", "Z9", 300.0), # 1 Transfer R2 -> R3 or R1 -> R3 (Moderate)
            ODPair("OD_1_6", "Z1", "Z6", 250.0), # 1 Transfer R3 -> R5
            ODPair("OD_3_1", "Z3", "Z1", 90.0),  # Not directly supported (stress test for engine)
            ODPair("OD_2_8", "Z2", "Z8", 380.0), # Direct R1 (Heavy)
            ODPair("OD_9_2", "Z9", "Z2", 150.0), # 1 Transfer R4 -> R2 (Hub 3 or 6)
            ODPair("OD_5_1", "Z5", "Z1", 60.0),  # Reverse R3 not exists -> R1 Z5->Z8 (wrong), so maybe no route. It's realistic!
        ]

        # 4. Generate Trips (Hành trình thực tế) for testing KPIs
        self.trips = [
            Trip([Leg("R1", r1_stops[0].id(), r1_stops[-1].id())]),
            Trip([Leg("R2", r2_stops[0].id(), r2_stops[-1].id())]),
            Trip([Leg("R3", r3_stops[0].id(), r3_stops[-1].id())]),
            Trip([Leg("R4", r4_stops[0].id(), r4_stops[-1].id())]),

            Trip([Leg("R5", r5_stops[0].id(), r5_stops[-1].id())]),
     
            Trip([
                Leg("R2", hubs["Z7"].id(), hubs["Z6"].id()),
                Leg("R4", hubs["Z6"].id(), hubs["Z3"].id())
            ])
        ]

    def get(self, reference=None) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips

    def get_od_matrix(self) -> ODMatrix:
        return ODMatrix(self.od_pairs, self.zones)
        
    def get_transit_network(self) -> TransitNetwork:
        return TransitNetwork(self.stops, self.routes)
