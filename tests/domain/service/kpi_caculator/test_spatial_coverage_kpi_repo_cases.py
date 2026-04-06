import pytest

from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator
from src.domain.model.leg import CandidateLeg
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.model.point import Point
from src.domain.model.route import Route
from src.domain.model.routing_result import EvaluatedRoutingOption
from src.domain.model.stop import Stop
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.trip import CandidateTrip, Trip
from src.domain.model.zone import Zone
from src.domain.service.kpi_caculator.spatial_coverage_kpi import SpatialCoverageCalculator


class _SpatialRepoBase:
    BASE_LAT = 21.0
    BASE_LON = 105.0

    def __init__(self):
        self.zones: list[Zone] = []
        self.od_pairs: list[ODPair] = []
        self.stops: list[Stop] = []
        self.routes: list[Route] = []
        self.trips: list[Trip] = []

    def p(self, x: int | float, y: int | float) -> Point:
        return Point(self.BASE_LAT + x / 100000.0, self.BASE_LON + y / 100000.0)

    def s(self, stop_id: str, x: int | float, y: int | float) -> Stop:
        return Stop(stop_id, self.BASE_LAT + x / 100000.0, self.BASE_LON + y / 100000.0)

    def get_od_matrix(self) -> ODMatrix:
        return ODMatrix(self.od_pairs, self.zones)

    def get_transit_network(self) -> TransitNetwork:
        return TransitNetwork(self.stops, self.routes)


class SpatialRepoCenter(_SpatialRepoBase):
    def __init__(self):
        super().__init__()
        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(100, 0), self.p(100, 100), self.p(0, 100)], self.p(50, 50)),
            Zone("Z2", [self.p(150, 0), self.p(250, 0), self.p(250, 100), self.p(150, 100)], self.p(200, 50)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_CENTER", 50, 50),
            self.s("S2_CENTER", 200, 50),
        ]
        self.routes = [Route("R1", [self.p(50, 50), self.p(200, 50)], ["S1_CENTER", "S2_CENTER"])]


class SpatialRepoEdge(_SpatialRepoBase):
    def __init__(self):
        super().__init__()
        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(100, 0), self.p(100, 100), self.p(0, 100)], self.p(50, 50)),
            Zone("Z2", [self.p(150, 0), self.p(250, 0), self.p(250, 100), self.p(150, 100)], self.p(200, 50)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_EDGE", 10, 50),
            self.s("S2_EDGE", 160, 50),
        ]
        self.routes = [Route("R1", [self.p(10, 50), self.p(160, 50)], ["S1_EDGE", "S2_EDGE"])]


class SpatialRepoOverlap(_SpatialRepoBase):
    def __init__(self):
        super().__init__()
        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(100, 0), self.p(100, 100), self.p(0, 100)], self.p(50, 50)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z1", 100)]
        self.stops = [
            self.s("S1_CENTER", 50, 50),
            self.s("S1_DUPLICATE", 50, 50),
            self.s("S1_NEAR", 70, 50),
        ]
        self.routes = []


class SpatialRepoFirstLastLegs(_SpatialRepoBase):
    def __init__(self):
        super().__init__()
        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(100, 0), self.p(100, 100), self.p(0, 100)], self.p(50, 50)),
            Zone("Z2", [self.p(150, 0), self.p(250, 0), self.p(250, 100), self.p(150, 100)], self.p(200, 50)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_EDGE", 10, 50),
            self.s("H1", 100, 120),
            self.s("S1_NOISE", 40, 40),
            self.s("S2_NOISE", 210, 40),
            self.s("H2", 150, 120),
            self.s("S2_EDGE", 160, 50),
        ]
        self.routes = [
            Route("R1", [self.p(10, 50), self.p(100, 120)], ["S1_EDGE", "H1"]),
            Route("R2", [self.p(40, 40), self.p(210, 40)], ["S1_NOISE", "S2_NOISE"]),
            Route("R3", [self.p(150, 120), self.p(160, 50)], ["H2", "S2_EDGE"]),
        ]


def _build_option(candidate_legs: list[CandidateLeg]) -> EvaluatedRoutingOption:
    return EvaluatedRoutingOption(CandidateTrip(candidate_legs), Trip([]))


def _zone(repo, zone_id: str):
    return repo.get_od_matrix().get_zone_by_id(zone_id)


def _stop(repo, stop_id: str):
    return repo.get_transit_network().get_stop_by_id(stop_id)


def test_center_stop_inside_zone_returns_partial_coverage():
    repo = SpatialRepoCenter()
    calc = SpatialCoverageCalculator()
    geometry_calculator = ShapelyGeometryCalculator()

    result = calc.calculate(
        _build_option([CandidateLeg("R1", {"S1_CENTER"}, {"S2_CENTER"})]),
        od_pair_id="OD1",
        od_matrix=repo.get_od_matrix(),
        transit_network=repo.get_transit_network(),
        geometry_calculator=geometry_calculator,
        radius_m=50.0,
    )

    assert 0.0 < result["origin_coverage_ratio"] < 1.0
    assert 0.0 < result["destination_coverage_ratio"] < 1.0
    assert result["score_ratio"] == pytest.approx(
        min(result["origin_coverage_ratio"], result["destination_coverage_ratio"])
    )
    assert result["origin_stop_count"] == 1
    assert result["destination_stop_count"] == 1


def test_large_radius_inside_zone_clamps_coverage_to_one():
    repo = SpatialRepoCenter()
    calc = SpatialCoverageCalculator()
    geometry_calculator = ShapelyGeometryCalculator()

    result = calc.calculate(
        _build_option([CandidateLeg("R1", {"S1_CENTER"}, {"S2_CENTER"})]),
        od_pair_id="OD1",
        od_matrix=repo.get_od_matrix(),
        transit_network=repo.get_transit_network(),
        geometry_calculator=geometry_calculator,
        radius_m=170.0,
    )

    assert result["origin_coverage_ratio"] == pytest.approx(1.0)
    assert result["destination_coverage_ratio"] == pytest.approx(1.0)
    assert result["score_ratio"] == pytest.approx(1.0)


def test_inside_stop_near_boundary_is_clipped_by_zone_boundary():
    centered_repo = SpatialRepoCenter()
    edge_repo = SpatialRepoEdge()
    geometry_calculator = ShapelyGeometryCalculator()

    centered_ratio = geometry_calculator.calculate_zone_coverage_ratio(
        _zone(centered_repo, "Z1"),
        [_stop(centered_repo, "S1_CENTER").coord()],
        radius_m=50.0,
    )
    edge_ratio = geometry_calculator.calculate_zone_coverage_ratio(
        _zone(edge_repo, "Z1"),
        [_stop(edge_repo, "S1_EDGE").coord()],
        radius_m=50.0,
    )

    assert 0.0 < edge_ratio < centered_ratio < 1.0


def test_overlapping_or_duplicate_inside_zone_buffers_do_not_double_count():
    repo = SpatialRepoOverlap()
    geometry_calculator = ShapelyGeometryCalculator()
    zone = _zone(repo, "Z1")
    single_point = _stop(repo, "S1_CENTER").coord()
    duplicate_point = _stop(repo, "S1_DUPLICATE").coord()
    nearby_point = _stop(repo, "S1_NEAR").coord()

    single_ratio = geometry_calculator.calculate_zone_coverage_ratio(
        zone, [single_point], radius_m=50.0
    )
    duplicate_ratio = geometry_calculator.calculate_zone_coverage_ratio(
        zone, [single_point, duplicate_point], radius_m=50.0
    )
    nearby_ratio = geometry_calculator.calculate_zone_coverage_ratio(
        zone, [single_point, nearby_point], radius_m=50.0
    )

    assert single_ratio == pytest.approx(duplicate_ratio, rel=1e-6, abs=1e-6)
    assert single_ratio < nearby_ratio <= 1.0


def test_spatial_kpi_uses_only_first_and_last_candidate_legs():
    repo = SpatialRepoFirstLastLegs()
    calc = SpatialCoverageCalculator()
    geometry_calculator = ShapelyGeometryCalculator()
    od_matrix = repo.get_od_matrix()
    transit_network = repo.get_transit_network()

    result = calc.calculate(
        _build_option(
            [
                CandidateLeg("R1", {"S1_EDGE"}, {"H1"}),
                CandidateLeg("R2", {"S1_NOISE"}, {"S2_NOISE"}),
                CandidateLeg("R3", {"H2"}, {"S2_EDGE"}),
            ]
        ),
        od_pair_id="OD1",
        od_matrix=od_matrix,
        transit_network=transit_network,
        geometry_calculator=geometry_calculator,
        radius_m=50.0,
    )

    expected_origin = geometry_calculator.calculate_zone_coverage_ratio(
        od_matrix.get_zone_by_id("Z1"),
        [transit_network.get_stop_by_id("S1_EDGE").coord()],
        radius_m=50.0,
    )
    expected_destination = geometry_calculator.calculate_zone_coverage_ratio(
        od_matrix.get_zone_by_id("Z2"),
        [transit_network.get_stop_by_id("S2_EDGE").coord()],
        radius_m=50.0,
    )

    assert result["origin_stop_count"] == 1
    assert result["destination_stop_count"] == 1
    assert result["origin_coverage_ratio"] == pytest.approx(expected_origin)
    assert result["destination_coverage_ratio"] == pytest.approx(expected_destination)
    assert result["score_ratio"] == pytest.approx(min(expected_origin, expected_destination))
