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


class FakeRepoSC1(AbstractRepository):
    """
    Spatial coverage case 1:
    - Stops are centered inside both OD zones.
    - Useful for partial coverage and full coverage with large radius.
    """

    def __init__(self):
        def P(x: int, y: int) -> Point:
            return Point(21.0 + x / 100000.0, 105.0 + y / 100000.0)

        def S(stop_id: str, x: int, y: int) -> Stop:
            return Stop(stop_id, 21.0 + x / 100000.0, 105.0 + y / 100000.0)

        self.zones = [
            Zone("Z1", [P(0, 0), P(0, 200), P(200, 200), P(200, 0)], P(100, 100)),
            Zone("Z2", [P(0, 400), P(0, 600), P(200, 600), P(200, 400)], P(100, 500)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            S("S1_CENTER", 100, 100),
            S("S2_CENTER", 100, 500),
        ]
        self.routes = [
            Route("R1", [P(100, 100), P(100, 500)], ["S1_CENTER", "S2_CENTER"]),
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
