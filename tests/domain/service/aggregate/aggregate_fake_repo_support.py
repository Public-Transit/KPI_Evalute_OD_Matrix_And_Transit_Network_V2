from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.model.point import Point
from src.domain.model.route import Route
from src.domain.model.stop import Stop
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.trip import Trip
from src.domain.model.zone import Zone
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


class _AggregateRepoBase:
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

    def get(self, reference=None):
        return self.stops, self.routes, self.zones, self.od_pairs, self.trips

    def get_od_matrix(self) -> ODMatrix:
        return ODMatrix(self.od_pairs, self.zones)

    def get_transit_network(self) -> TransitNetwork:
        return TransitNetwork(self.stops, self.routes)


class AggregateRepoAG1(_AggregateRepoBase):
    def __init__(self):
        super().__init__()
        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(100, 0), self.p(100, 100), self.p(0, 100)], self.p(50, 50)),
            Zone("Z2", [self.p(300, 0), self.p(400, 0), self.p(400, 100), self.p(300, 100)], self.p(350, 50)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_CENTER", 50, 50),
            self.s("S2_CENTER", 350, 50),
        ]
        self.routes = [
            Route("R_DIRECT_GOOD", [self.p(50, 50), self.p(350, 50)], ["S1_CENTER", "S2_CENTER"]),
        ]


class AggregateRepoAG2(_AggregateRepoBase):
    def __init__(self):
        super().__init__()
        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(145, 0), self.p(145, 145), self.p(0, 145)], self.p(72.5, 72.5)),
            Zone("Z2", [self.p(300, 227), self.p(445, 227), self.p(445, 372), self.p(300, 372)], self.p(372.5, 299.5)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_ORIGIN", 73, 73),
            self.s("H_TRANSFER", 73, 300),
            self.s("S2_DEST", 373, 300),
        ]
        self.routes = [
            Route("R_FEEDER", [self.p(73, 73), self.p(73, 300)], ["S1_ORIGIN", "H_TRANSFER"]),
            Route("R_TRUNK", [self.p(73, 300), self.p(373, 300)], ["H_TRANSFER", "S2_DEST"]),
        ]


class AggregateRepoAG3(_AggregateRepoBase):
    def __init__(self):
        super().__init__()
        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(100, 0), self.p(100, 100), self.p(0, 100)], self.p(50, 50)),
            Zone("Z2", [self.p(300, 0), self.p(400, 0), self.p(400, 100), self.p(300, 100)], self.p(350, 50)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_DIRECT", 50, 50),
            self.s("S2_DIRECT", 350, 50),
            self.s("S1_EDGE", 20, 20),
            self.s("H_TRANSFER", 20, 200),
            self.s("S2_EDGE", 350, 20),
        ]
        self.routes = [
            Route("R_DIRECT", [self.p(50, 50), self.p(350, 50)], ["S1_DIRECT", "S2_DIRECT"]),
            Route("R_TRANSFER_1", [self.p(20, 20), self.p(20, 200)], ["S1_EDGE", "H_TRANSFER"]),
            Route("R_TRANSFER_2", [self.p(20, 200), self.p(350, 200), self.p(350, 20)], ["H_TRANSFER", "S2_EDGE"]),
        ]


class AggregateRepoAG4(_AggregateRepoBase):
    def __init__(self):
        super().__init__()
        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(200, 0), self.p(200, 200), self.p(0, 200)], self.p(100, 100)),
            Zone("Z2", [self.p(400, 0), self.p(600, 0), self.p(600, 200), self.p(400, 200)], self.p(500, 100)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_CENTER_A", 100, 100),
            self.s("S2_CENTER_A", 500, 100),
            self.s("S1_CENTER_B", 100, 100),
            self.s("S2_CENTER_B", 500, 100),
        ]
        self.routes = [
            Route("R_LOW_COVERAGE", [self.p(100, 100), self.p(500, 100)], ["S1_CENTER_A", "S2_CENTER_A"]),
            Route("R_HIGH_CIRCUITY", [self.p(100, 100), self.p(100, 500), self.p(500, 500), self.p(500, 100)], ["S1_CENTER_B", "S2_CENTER_B"]),
        ]


class AggregateRepoAG5(_AggregateRepoBase):
    def __init__(self):
        super().__init__()
        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(100, 0), self.p(100, 100), self.p(0, 100)], self.p(50, 50)),
            Zone("Z2", [self.p(300, 0), self.p(400, 0), self.p(400, 100), self.p(300, 100)], self.p(350, 50)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_A", 50, 50),
            self.s("S2_A", 350, 50),
            self.s("S1_B", 50, 50),
            self.s("S2_B", 350, 50),
            self.s("S1_C", 50, 50),
            self.s("S2_C", 350, 50),
        ]
        self.routes = [
            Route("R_BEST_A", [self.p(50, 50), self.p(350, 50)], ["S1_A", "S2_A"]),
            Route("R_BEST_B", [self.p(50, 50), self.p(350, 50)], ["S1_B", "S2_B"]),
            Route("R_WORSE_C", [self.p(50, 50), self.p(200, 200), self.p(350, 50)], ["S1_C", "S2_C"]),
        ]


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
        repo_factory=AggregateRepoAG1,
        image_name="plot_aggregate_case_1.png",
        highlight_stop_ids=["S1_CENTER", "S2_CENTER"],
    ),
    AggregateCaseDefinition(
        case_id="AG2",
        title="Weak But Valid OD",
        repo_factory=AggregateRepoAG2,
        image_name="plot_aggregate_case_2.png",
        highlight_stop_ids=["S1_ORIGIN", "H_TRANSFER", "S2_DEST"],
    ),
    AggregateCaseDefinition(
        case_id="AG3",
        title="Mixed OD",
        repo_factory=AggregateRepoAG3,
        image_name="plot_aggregate_case_3.png",
        highlight_stop_ids=["S1_DIRECT", "S2_DIRECT", "S1_EDGE", "H_TRANSFER", "S2_EDGE"],
    ),
    AggregateCaseDefinition(
        case_id="AG4",
        title="All Trips Filtered Out",
        repo_factory=AggregateRepoAG4,
        image_name="plot_aggregate_case_4.png",
        highlight_stop_ids=["S1_CENTER_A", "S2_CENTER_A", "S1_CENTER_B", "S2_CENTER_B"],
    ),
    AggregateCaseDefinition(
        case_id="AG5",
        title="Tie Stability",
        repo_factory=AggregateRepoAG5,
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
        raise AssertionError("Each aggregate test repo must expose exactly one OD pair")

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
