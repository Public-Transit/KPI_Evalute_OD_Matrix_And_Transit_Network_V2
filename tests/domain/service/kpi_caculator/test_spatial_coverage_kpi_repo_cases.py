import pytest

from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator
from src.adapters.repository.fake_repo_sc1 import FakeRepoSC1
from src.adapters.repository.fake_repo_sc2 import FakeRepoSC2
from src.adapters.repository.fake_repo_sc3 import FakeRepoSC3
from src.adapters.repository.fake_repo_sc4 import FakeRepoSC4
from src.domain.model.leg import CandidateLeg
from src.domain.model.routing_result import EvaluatedRoutingOption
from src.domain.model.trip import CandidateTrip, Trip
from src.domain.service.kpi_caculator.spatial_coverage_kpi import SpatialCoverageCalculator


EXPECTED_CENTER_COVERAGE = 0.16982907741291478
EXPECTED_EDGE_COVERAGE = 0.1314002742228597
EXPECTED_OVERLAP_COVERAGE = 0.2175569835770958


def _build_option(candidate_legs: list[CandidateLeg]) -> EvaluatedRoutingOption:
    return EvaluatedRoutingOption(CandidateTrip(candidate_legs), Trip([]))


def _zone(repo, zone_id: str):
    return repo.get_od_matrix().get_zone_by_id(zone_id)


def _stop(repo, stop_id: str):
    return repo.get_transit_network().get_stop_by_id(stop_id)


def test_center_stop_inside_zone_returns_expected_partial_coverage():
    repo = FakeRepoSC1()
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

    assert result["origin_coverage_ratio"] == pytest.approx(
        EXPECTED_CENTER_COVERAGE, rel=1e-3, abs=1e-4
    )
    assert result["destination_coverage_ratio"] == pytest.approx(
        EXPECTED_CENTER_COVERAGE, rel=1e-3, abs=1e-4
    )
    assert result["score_ratio"] == pytest.approx(
        EXPECTED_CENTER_COVERAGE * EXPECTED_CENTER_COVERAGE, rel=1e-3, abs=1e-4
    )
    assert result["origin_stop_count"] == 1
    assert result["destination_stop_count"] == 1


def test_large_radius_inside_zone_clamps_coverage_to_one():
    repo = FakeRepoSC1()
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
    centered_repo = FakeRepoSC1()
    edge_repo = FakeRepoSC2()
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

    assert centered_ratio == pytest.approx(EXPECTED_CENTER_COVERAGE, rel=1e-3, abs=1e-4)
    assert edge_ratio == pytest.approx(EXPECTED_EDGE_COVERAGE, rel=1e-3, abs=1e-4)
    assert 0.0 < edge_ratio < centered_ratio


def test_overlapping_or_duplicate_inside_zone_buffers_do_not_double_count():
    repo = FakeRepoSC3()
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

    assert single_ratio == pytest.approx(EXPECTED_CENTER_COVERAGE, rel=1e-3, abs=1e-4)
    assert duplicate_ratio == pytest.approx(single_ratio, rel=1e-6, abs=1e-6)
    assert nearby_ratio == pytest.approx(EXPECTED_OVERLAP_COVERAGE, rel=1e-3, abs=1e-4)
    assert single_ratio < nearby_ratio < single_ratio * 2


def test_spatial_kpi_uses_only_first_and_last_candidate_legs():
    repo = FakeRepoSC4()
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

    assert expected_origin == pytest.approx(EXPECTED_EDGE_COVERAGE, rel=1e-3, abs=1e-4)
    assert expected_destination == pytest.approx(EXPECTED_EDGE_COVERAGE, rel=1e-3, abs=1e-4)
    assert result["origin_stop_count"] == 1
    assert result["destination_stop_count"] == 1
    assert result["origin_coverage_ratio"] == pytest.approx(
        expected_origin, rel=1e-3, abs=1e-4
    )
    assert result["destination_coverage_ratio"] == pytest.approx(
        expected_destination, rel=1e-3, abs=1e-4
    )
    assert result["score_ratio"] == pytest.approx(
        expected_origin * expected_destination, rel=1e-3, abs=1e-4
    )
