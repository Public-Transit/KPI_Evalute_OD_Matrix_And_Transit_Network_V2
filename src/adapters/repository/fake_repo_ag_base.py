from __future__ import annotations

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


class FakeRepoAGBase(AbstractRepository):
    BASE_LAT = 21.0
    BASE_LON = 105.0

    def __init__(self) -> None:
        self.zones: list[Zone] = []
        self.od_pairs: list[ODPair] = []
        self.stops: list[Stop] = []
        self.routes: list[Route] = []
        self.trips: list[Trip] = []

    def p(self, x: int | float, y: int | float) -> Point:
        return Point(self.BASE_LAT + x / 100000.0, self.BASE_LON + y / 100000.0)

    def s(self, stop_id: str, x: int | float, y: int | float) -> Stop:
        return Stop(stop_id, self.BASE_LAT + x / 100000.0, self.BASE_LON + y / 100000.0)

    def get(
        self, reference=None
    ) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips

    def get_od_matrix(self) -> ODMatrix:
        return ODMatrix(self.od_pairs, self.zones)

    def get_transit_network(self) -> TransitNetwork:
        return TransitNetwork(self.stops, self.routes)
