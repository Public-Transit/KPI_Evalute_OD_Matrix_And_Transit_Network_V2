from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator
from src.adapters.repository.fake_repo_ag1 import FakeRepoAG1
from src.adapters.repository.fake_repo_ag2 import FakeRepoAG2
from src.adapters.repository.fake_repo_ag3 import FakeRepoAG3
from src.adapters.repository.fake_repo_ag4 import FakeRepoAG4
from src.adapters.repository.fake_repo_ag5 import FakeRepoAG5
from src.domain.service.aggregate.composite_quality_index import (
    CompositeQualityIndexCalculator,
)
from src.domain.service.aggregate.od_kpi_aggregator import ODKPIAggregator
from src.domain.service.filter import MinDistanceCandidateTripFilterV2
from src.domain.service.generate_od_routing_result import GenerateODRoutingResultService
from src.domain.service.kpi_caculator.circuity_kpi import CircuityIndexCalculator
from src.domain.service.kpi_caculator.spatial_coverage_kpi import (
    SpatialCoverageCalculator,
)
from src.domain.service.kpi_caculator.transfer_kpi import TransferRateCalculator
from src.domain.service.routing import CombinedRoutingEngine


@dataclass(frozen=True)
class AggregateCaseDefinition:
    case_id: str
    title: str
    repo_factory: type
    image_name: str
    highlight_stop_ids: list[str]


AGGREGATE_CASES = [
    AggregateCaseDefinition(
        case_id="AG1",
        title="Excellent Direct OD",
        repo_factory=FakeRepoAG1,
        image_name="plot_aggregate_case_1.png",
        highlight_stop_ids=["S1_CENTER", "S2_CENTER"],
    ),
    AggregateCaseDefinition(
        case_id="AG2",
        title="Weak But Valid OD",
        repo_factory=FakeRepoAG2,
        image_name="plot_aggregate_case_2.png",
        highlight_stop_ids=["S1_ORIGIN", "H_TRANSFER", "S2_DEST"],
    ),
    AggregateCaseDefinition(
        case_id="AG3",
        title="Mixed OD",
        repo_factory=FakeRepoAG3,
        image_name="plot_aggregate_case_3.png",
        highlight_stop_ids=["S1_DIRECT", "S2_DIRECT", "S1_EDGE", "H_TRANSFER", "S2_EDGE"],
    ),
    AggregateCaseDefinition(
        case_id="AG4",
        title="All Trips Filtered Out",
        repo_factory=FakeRepoAG4,
        image_name="plot_aggregate_case_4.png",
        highlight_stop_ids=["S1_CENTER_A", "S2_CENTER_A", "S1_CENTER_B", "S2_CENTER_B"],
    ),
    AggregateCaseDefinition(
        case_id="AG5",
        title="Tie Stability",
        repo_factory=FakeRepoAG5,
        image_name="plot_aggregate_case_5.png",
        highlight_stop_ids=["S1_A", "S2_A", "S1_B", "S2_B", "S1_C", "S2_C"],
    ),
]


def run_aggregate_case(repo) -> dict[str, Any]:
    geometry_calculator = ShapelyGeometryCalculator()
    routing_service = GenerateODRoutingResultService(
        CombinedRoutingEngine(), MinDistanceCandidateTripFilterV2()
    )
    transfer_calc = TransferRateCalculator()
    circuity_calc = CircuityIndexCalculator()
    spatial_calc = SpatialCoverageCalculator()
    composite_calc = CompositeQualityIndexCalculator()
    od_aggregator = ODKPIAggregator()

    od_matrix = repo.get_od_matrix()
    transit_network = repo.get_transit_network()
    routing_results = routing_service.generate_od_routing_result(
        od_matrix, transit_network, geometry_calculator
    )

    if len(routing_results) != 1:
        raise AssertionError("Each aggregate fake repo must expose exactly one OD pair")

    routing_result = routing_results[0]
    option_results = []
    trip_kpi_results = []

    for option_index, evaluated_option in enumerate(
        routing_result.evaluated_routing_options(), start=1
    ):
        transfer_result = transfer_calc.calculate(evaluated_option)
        circuity_result = circuity_calc.calculate(
            evaluated_option,
            transit_network=transit_network,
            geometry_calculator=geometry_calculator,
        )
        spatial_result = spatial_calc.calculate(
            evaluated_option,
            od_pair_id=routing_result.od_pair_id(),
            od_matrix=od_matrix,
            transit_network=transit_network,
            geometry_calculator=geometry_calculator,
        )
        composite_result = composite_calc.calculate(
            transfer_result.get("score"),
            circuity_result.get("score"),
            spatial_result.get("score_ratio"),
        )

        representative_trip = evaluated_option.representative_trip()
        route_ids = (
            [leg.route_id for leg in representative_trip.legs]
            if representative_trip and representative_trip.legs
            else []
        )
        passed_hard_threshold = (
            transfer_result.get("score") in (0, 1)
            and isinstance(circuity_result.get("score"), (int, float))
            and circuity_result.get("score") <= 2.5
            and isinstance(spatial_result.get("score_ratio"), (int, float))
            and spatial_result.get("score_ratio") >= 0.1
            and composite_result.get("score") is not None
        )

        option_summary = {
            "option_id": f"OPT{option_index}",
            "routes": route_ids,
            "transfer_kpi": transfer_result,
            "circuity_kpi": circuity_result,
            "spatial_coverage_kpi": spatial_result,
            "composite_kpi": composite_result,
            "passed_hard_threshold": passed_hard_threshold,
        }
        option_results.append(option_summary)
        trip_kpi_results.append(
            {
                "transfer_kpi": transfer_result,
                "circuity_kpi": circuity_result,
                "spatial_coverage_kpi": spatial_result,
                "composite_kpi": composite_result,
            }
        )

    aggregated_kpis = od_aggregator.calculate(trip_kpi_results)

    return {
        "od_pair_id": routing_result.od_pair_id(),
        "option_results": option_results,
        "aggregated_kpis": aggregated_kpis,
        "trip_count": len(option_results),
        "valid_trip_count": sum(
            1 for option_result in option_results if option_result["passed_hard_threshold"]
        ),
    }
