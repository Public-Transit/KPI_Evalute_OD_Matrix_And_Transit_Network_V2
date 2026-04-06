from typing import Any

from src.domain.model.od_matrix import ODMatrix
from src.domain.model.routing_result import EvaluatedRoutingOption
from src.domain.model.transit_network import TransitNetwork
from src.domain.port import IGeometryCalculator
from src.domain.service.kpi_caculator.kpi_base import KPICalculator


class SpatialCoverageCalculator(KPICalculator):
    def calculate(self, evaluated_routing_option: EvaluatedRoutingOption, **kwargs) -> dict[str, Any]:
        """
        Calculate OD spatial coverage using one candidate trip:
        - Take the first CandidateLeg for origin boarding stops
        - Take the last CandidateLeg for destination alighting stops
        - Compute zone coverage ratio for origin/destination
        - Final score = clamp(min(origin_ratio, destination_ratio))
        """
        od_pair_id: str = kwargs.get("od_pair_id")
        od_matrix: ODMatrix = kwargs.get("od_matrix")
        transit_network: TransitNetwork = kwargs.get("transit_network")
        geometry_calculator: IGeometryCalculator = kwargs.get("geometry_calculator")
        radius_m: float = kwargs.get("radius_m", 50.0)

        if not all([od_pair_id, od_matrix, transit_network, geometry_calculator]):
            raise ValueError("od_pair_id, od_matrix, transit_network and geometry_calculator are required")

        od_pair = od_matrix.get_od_pair_by_id(od_pair_id)
        if not od_pair:
            raise ValueError(f"Cannot find OD pair with id {od_pair_id}")

        origin_zone = od_matrix.get_zone_by_id(od_pair.origin_zone_id())
        dest_zone = od_matrix.get_zone_by_id(od_pair.destination_zone_id())
        if not origin_zone or not dest_zone:
            raise ValueError(f"Cannot find origin/destination zone for OD pair {od_pair_id}")

        candidate_trip = evaluated_routing_option.candidate_trip()
        if not candidate_trip or not candidate_trip.candidate_legs:
            return {
                "score_ratio": 0.0,
                "origin_coverage_ratio": 0.0,
                "destination_coverage_ratio": 0.0,
                "origin_zone_id": origin_zone.id(),
                "destination_zone_id": dest_zone.id(),
                "radius_m": radius_m,
                "origin_stop_count": 0,
                "destination_stop_count": 0,
            }

        first_leg = candidate_trip.candidate_legs[0]
        last_leg = candidate_trip.candidate_legs[-1]
        origin_stop_ids = set(first_leg.possible_boarding_stop_ids or set())
        destination_stop_ids = set(last_leg.possible_alighting_stop_ids or set())

        origin_points = []
        for stop_id in origin_stop_ids:
            stop = transit_network.get_stop_by_id(stop_id)
            if stop:
                origin_points.append(stop.coord())

        destination_points = []
        for stop_id in destination_stop_ids:
            stop = transit_network.get_stop_by_id(stop_id)
            if stop:
                destination_points.append(stop.coord())

        origin_coverage_ratio = origin_zone.calculate_zone_coverage_ratio(
            points=origin_points,
            radius_m=radius_m,
            geometry_calculator=geometry_calculator,
        )
        destination_coverage_ratio = dest_zone.calculate_zone_coverage_ratio(
            points=destination_points,
            radius_m=radius_m,
            geometry_calculator=geometry_calculator,
        )

        score_ratio = max(0.0, min(1.0, min(origin_coverage_ratio, destination_coverage_ratio)))

        return {
            "score_ratio": score_ratio,
            "origin_coverage_ratio": origin_coverage_ratio,
            "destination_coverage_ratio": destination_coverage_ratio,
            "origin_zone_id": origin_zone.id(),
            "destination_zone_id": dest_zone.id(),
            "radius_m": radius_m,
            "origin_stop_count": len(origin_points),
            "destination_stop_count": len(destination_points),
        }
