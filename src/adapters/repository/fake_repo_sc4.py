from typing import Tuple

from src.adapters.repository.abstract_repository import AbstractRepository
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.model.point import Point
from src.domain.model.route import Route
from src.domain.model.stop import Stop
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.trip import Trip
from src.domain.model.zone import Zone


class FakeRepoSC4(AbstractRepository):
    """
    Spatial coverage case 4:
    - Three-leg network used to verify only first-leg boarding and
      last-leg alighting stops contribute to coverage.
    - Middle leg carries noise stops that would change the ratio if used.
    """

    def __init__(self):
        def P(x: int, y: int) -> Point:
            return Point(21.0 + x / 100000.0, 105.0 + y / 100000.0)

        def S(stop_id: str, x: int, y: int) -> Stop:
            return Stop(stop_id, 21.0 + x / 100000.0, 105.0 + y / 100000.0)

        self.zones = [
            Zone("Z1", [P(0, 0), P(0, 200), P(200, 200), P(200, 0)], P(100, 100)),
            Zone("ZH1", [P(0, 400), P(0, 600), P(200, 600), P(200, 400)], P(100, 500)),
            Zone("ZH2", [P(0, 800), P(0, 1000), P(200, 1000), P(200, 800)], P(100, 900)),
            Zone("Z2", [P(0, 1200), P(0, 1400), P(200, 1400), P(200, 1200)], P(100, 1300)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            S("S1_EDGE", 20, 100),
            S("S1_NOISE", 100, 100),
            S("H1", 100, 500),
            S("H2", 100, 900),
            S("S2_NOISE", 100, 1300),
            S("S2_EDGE", 20, 1300),
        ]
        self.routes = [
            Route("R1", [P(20, 100), P(100, 500)], ["S1_EDGE", "H1"]),
            Route("R2", [P(100, 100), P(100, 1300)], ["S1_NOISE", "S2_NOISE"]),
            Route("R3", [P(100, 900), P(20, 1300)], ["H2", "S2_EDGE"]),
        ]
        self.trips: list[Trip] = []

    def get(
        self, reference=None
    ) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips

    def get_od_matrix(self) -> ODMatrix:
        return ODMatrix(self.od_pairs, self.zones)

    def get_transit_network(self) -> TransitNetwork:
        return TransitNetwork(self.stops, self.routes)
