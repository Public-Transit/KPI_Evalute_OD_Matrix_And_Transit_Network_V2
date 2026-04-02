from typing import Tuple

from src.adapters.repository.abstract_repository import AbstractRepository
from src.domain.model.leg import Leg
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.model.point import Point
from src.domain.model.route import Route
from src.domain.model.stop import Stop
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.trip import Trip
from src.domain.model.zone import Zone


class FakeRepoGrid3x3(AbstractRepository):
    """
    Lightweight placeholder network for local experimentation.

    The filename is kept for compatibility, but the data is intentionally small and
    deterministic so both APIs can be exercised without relying on large fake-case
    catalogs.
    """

    BASE_LAT = 21.0
    BASE_LON = 105.0

    def __init__(self, seed: int | None = None):
        del seed

        def point(x_m: float, y_m: float) -> Point:
            return Point(
                self.BASE_LAT + x_m / 100000.0,
                self.BASE_LON + y_m / 100000.0,
            )

        def stop(stop_id: str, x_m: float, y_m: float) -> Stop:
            return Stop(
                stop_id,
                self.BASE_LAT + x_m / 100000.0,
                self.BASE_LON + y_m / 100000.0,
            )

        self.zones = [
            Zone(
                "Z1",
                [point(0, 0), point(100, 0), point(100, 100), point(0, 100)],
                point(50, 50),
            ),
            Zone(
                "Z2",
                [point(120, 0), point(220, 0), point(220, 100), point(120, 100)],
                point(170, 50),
            ),
        ]

        self.stops = [
            stop("S1", 20, 50),
            stop("S2", 80, 50),
            stop("S3", 140, 50),
            stop("S4", 200, 50),
            stop("S5", 170, 80),
        ]

        self.routes = [
            Route(
                "R1",
                [self._stop_coord("S1"), self._stop_coord("S2"), self._stop_coord("S3"), self._stop_coord("S4")],
                ["S1", "S2", "S3", "S4"],
            ),
            Route(
                "R2",
                [self._stop_coord("S3"), self._stop_coord("S5")],
                ["S3", "S5"],
            ),
        ]

        self.od_pairs = [
            ODPair("OD1", "Z1", "Z2", 120.0),
        ]

        self.trips = [
            Trip([Leg("R2", "S3", "S5")]),
            Trip([Leg("R1", "S1", "S4")]),
        ]

    def _stop_coord(self, stop_id: str) -> Point:
        for stop in self.stops:
            if stop.id() == stop_id:
                return stop.coord()
        raise ValueError(f"Cannot find stop with id {stop_id}")

    def get(
        self, reference=None
    ) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips

    def get_od_matrix(self) -> ODMatrix:
        return ODMatrix(self.od_pairs, self.zones)

    def get_transit_network(self) -> TransitNetwork:
        return TransitNetwork(self.stops, self.routes)
