from typing import Any

from src.domain.model.od_matrix import ODMatrix
from src.domain.model.routing_result import ODRoutingResult
from src.domain.model.transit_network import TransitNetwork
from src.domain.port import IGeometryCalculator
from src.domain.service.kpi_caculator.kpi_base import KPICalculator


class SpatialCoverageCalculator(KPICalculator):
    def calculate(self, routing_result: ODRoutingResult, **kwargs) -> dict[str, Any]:
        """
        Calculate OD spatial coverage using all candidate trips:
        - Take first CandidateLeg of each CandidateTrip for origin boarding stops
        - Take last CandidateLeg of each CandidateTrip for destination alighting stops
        - Compute zone coverage ratio for origin/destination
        - Final score = clamp(origin_ratio * destination_ratio)
        """
        od_matrix: ODMatrix = kwargs.get("od_matrix")
        transit_network: TransitNetwork = kwargs.get("transit_network")
        geometry_calculator: IGeometryCalculator = kwargs.get("geometry_calculator")
        radius_m: float = kwargs.get("radius_m", 500.0)

        if not all([od_matrix, transit_network, geometry_calculator]):
            raise ValueError("od_matrix, transit_network and geometry_calculator are required")

        od_pair_id = routing_result.od_pair_id()
        od_pair = od_matrix.get_od_pair_by_id(od_pair_id)
        if not od_pair:
            raise ValueError(f"Cannot find OD pair with id {od_pair_id}")

        origin_zone = od_matrix.get_zone_by_id(od_pair.origin_zone_id())
        dest_zone = od_matrix.get_zone_by_id(od_pair.destination_zone_id())
        if not origin_zone or not dest_zone:
            raise ValueError(f"Cannot find origin/destination zone for OD pair {od_pair_id}")

        candidate_trips = routing_result.candidate_trip()
        if not candidate_trips:
            return {
                "score_percent": 0.0,
                "score_ratio": 0.0,
                "origin_coverage_percent": 0.0,
                "origin_coverage_ratio": 0.0,
                "destination_coverage_percent": 0.0,
                "destination_coverage_ratio": 0.0,
                "origin_zone_id": origin_zone.id(),
                "destination_zone_id": dest_zone.id(),
                "radius_m": radius_m,
                "origin_stop_count": 0,
                "destination_stop_count": 0,
            }

        if isinstance(candidate_trips, list):
            candidate_trip_list = candidate_trips
        else:
            candidate_trip_list = [candidate_trips]

        origin_stop_ids: set[str] = set()
        destination_stop_ids: set[str] = set()

        for candidate_trip in candidate_trip_list:
            if not candidate_trip:
                continue
            candidate_legs = getattr(candidate_trip, "candidate_legs", None)
            if not candidate_legs:
                continue

            first_leg = candidate_legs[0]
            last_leg = candidate_legs[-1]

            origin_stop_ids.update(getattr(first_leg, "possible_boarding_stop_ids", set()) or set())
            destination_stop_ids.update(getattr(last_leg, "possible_alighting_stop_ids", set()) or set())

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

        score_ratio = max(0.0, min(1.0, origin_coverage_ratio * destination_coverage_ratio))

        return {
            "score_percent": score_ratio * 100.0,
            "score_ratio": score_ratio,
            "origin_coverage_percent": origin_coverage_ratio * 100.0,
            "origin_coverage_ratio": origin_coverage_ratio,
            "destination_coverage_percent": destination_coverage_ratio * 100.0,
            "destination_coverage_ratio": destination_coverage_ratio,
            "origin_zone_id": origin_zone.id(),
            "destination_zone_id": dest_zone.id(),
            "radius_m": radius_m,
            "origin_stop_count": len(origin_points),
            "destination_stop_count": len(destination_points),
        }
