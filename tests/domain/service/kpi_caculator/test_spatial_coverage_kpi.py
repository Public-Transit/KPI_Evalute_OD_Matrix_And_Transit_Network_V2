import pytest

from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator
from src.domain.model.leg import CandidateLeg
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.model.point import Point
from src.domain.model.routing_result_v2 import EvaluatedRoutingOption
from src.domain.model.stop import Stop
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.trip import CandidateTrip, Trip
from src.domain.model.zone import Zone
from src.domain.service.kpi_caculator.spatial_coverage_kpi import SpatialCoverageCalculator
from tests.domain.mock_geometry import MockGeometryCalculator


def test_spatial_coverage_calculator_uses_candidate_trip_endpoints():
    calc = SpatialCoverageCalculator()

    stops = [
        Stop("S1", 1.0, 1.0),
        Stop("S2", 1.1, 1.1),
        Stop("S3", 2.0, 2.0),
        Stop("S4", 2.1, 2.1),
        Stop("S5", 1.5, 1.5),
    ]
    transit_network = TransitNetwork(stops, [])

    # Boundaries are not used by MockGeometryCalculator coverage method.
    z1 = Zone("Z1", [], Point(1.0, 1.0))
    z2 = Zone("Z2", [], Point(2.0, 2.0))
    od1 = ODPair("OD1", "Z1", "Z2", 10)
    od_matrix = ODMatrix([od1], [z1, z2])

    candidate_trip = CandidateTrip([
        CandidateLeg("R1", {"S1", "S2"}, {"S5"}),
        CandidateLeg("R2", {"S2"}, {"S5"}),
        CandidateLeg("R3", {"S5"}, {"S3", "S4"}),
    ])
    evaluated_option = EvaluatedRoutingOption(candidate_trip, Trip([]))

    kpi_res = calc.calculate(
        evaluated_option,
        od_pair_id="OD1",
        od_matrix=od_matrix,
        transit_network=transit_network,
        geometry_calculator=MockGeometryCalculator(),
        radius_m=500.0,
    )

    # MockGeometryCalculator returns 0.5 coverage regardless of points.
    assert kpi_res["origin_coverage_ratio"] == 0.5
    assert kpi_res["destination_coverage_ratio"] == 0.5
    assert kpi_res["score_ratio"] == 0.25
    assert "score_percent" not in kpi_res
    assert "origin_coverage_percent" not in kpi_res
    assert "destination_coverage_percent" not in kpi_res

    # Validate that endpoints are collected from candidate trips as expected.
    assert kpi_res["origin_stop_count"] == 2  # S1, S2
    assert kpi_res["destination_stop_count"] == 2  # S3, S4


def test_spatial_coverage_calculator_returns_zero_when_no_candidate_trip():
    calc = SpatialCoverageCalculator()
    transit_network = TransitNetwork([Stop("S1", 1.0, 1.0)], [])
    z1 = Zone("Z1", [], Point(1.0, 1.0))
    z2 = Zone("Z2", [], Point(2.0, 2.0))
    od1 = ODPair("OD1", "Z1", "Z2", 10)
    od_matrix = ODMatrix([od1], [z1, z2])

    evaluated_option = EvaluatedRoutingOption(CandidateTrip([]), Trip([]))

    kpi_res = calc.calculate(
        evaluated_option,
        od_pair_id="OD1",
        od_matrix=od_matrix,
        transit_network=transit_network,
        geometry_calculator=MockGeometryCalculator(),
        radius_m=500.0,
    )

    assert kpi_res["score_ratio"] == 0.0
    assert "score_percent" not in kpi_res
    assert "origin_coverage_percent" not in kpi_res
    assert "destination_coverage_percent" not in kpi_res
    assert kpi_res["origin_stop_count"] == 0
    assert kpi_res["destination_stop_count"] == 0


def test_zone_coverage_does_not_double_count_overlapping_buffers():
    calc = ShapelyGeometryCalculator()
    zone = Zone(
        "Z",
        [Point(0.0, 0.0), Point(0.0, 0.01), Point(0.01, 0.01), Point(0.01, 0.0)],
        Point(0.005, 0.005),
    )
    p = Point(0.005, 0.005)

    single = calc.calculate_zone_coverage_ratio(zone, [p], radius_m=200.0)
    duplicated = calc.calculate_zone_coverage_ratio(zone, [p, p], radius_m=200.0)

    assert duplicated == pytest.approx(single)
