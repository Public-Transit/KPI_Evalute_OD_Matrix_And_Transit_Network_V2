# src/service_layer/service/trip_kpi_services.py
from numbers import Real

from src.domain.port import IGeometryCalculator
from src.domain.service.filter import AbstractCandidateTripFilterV2
from src.domain.service.generate_od_routing_result import GenerateODRoutingResultService
from src.domain.service.routing import AbstractRouting
from src.domain.service.trip_kpi_caculator.trip_kpi_base import TripKPICalculator
from src.service_layer.unit_of_work import AbstractUnitOfWork


def _build_trip_path(trip) -> dict[str, list[str]]:
    if not trip.legs:
        return {
            "route_sequence": [],
            "stop_sequence": [],
        }

    return {
        "route_sequence": [leg.route_id for leg in trip.legs],
        "stop_sequence": [leg.board_stop_id for leg in trip.legs]
        + [trip.legs[-1].alight_stop_id],
    }


def _coerce_numeric(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    return float(value)


def _build_trip_summary(total_demand: float | None) -> dict:
    return {
        "is_valid": total_demand is not None,
        "reason": None if total_demand is not None else "Trip KPI could not be calculated.",
        "scores": {
            "total_potential_demand": total_demand,
        },
    }


def _extract_total_potential_demand_result(kpi_result) -> tuple[float | None, list[dict]]:
    if not isinstance(kpi_result, dict):
        return None, []

    total_demand = _coerce_numeric(kpi_result.get("total_demand"))
    served_od_pairs = kpi_result.get("served_od_details")
    if not isinstance(served_od_pairs, list):
        served_od_pairs = []

    return total_demand, served_od_pairs


def _trip_sort_key(result: dict) -> tuple[bool, float]:
    total_demand = result["summary"]["scores"]["total_potential_demand"]
    if total_demand is None:
        return True, 0.0
    return False, -float(total_demand)


def _trip_signature(trip) -> tuple[tuple[str, str, str], ...]:
    return tuple((leg.route_id, leg.board_stop_id, leg.alight_stop_id) for leg in trip.legs)


def _collect_representative_trips(routing_results) -> list:
    unique_trips_by_signature = {}

    for routing_result in routing_results:
        for evaluated_option in routing_result.evaluated_routing_options():
            representative_trip = evaluated_option.representative_trip()
            if not representative_trip or not representative_trip.legs:
                continue

            signature = _trip_signature(representative_trip)
            if signature not in unique_trips_by_signature:
                unique_trips_by_signature[signature] = representative_trip

    return list(unique_trips_by_signature.values())


def calculate_kpis_for_all_trips(
    kpi_calculators: list[TripKPICalculator],
    uow: AbstractUnitOfWork,
    routing_engine: AbstractRouting,
    filter_engine: AbstractCandidateTripFilterV2,
    geometry_calculator: IGeometryCalculator,
    reference_path: str,
) -> list[dict]:
    """
    Calculate concise trip-level KPI results for representative trips generated from OD routing.
    """
    with uow:
        stops, routes, zones, od_pairs = uow.repo.get(reference_path)
        transit_network_factory = getattr(uow.repo, "get_transit_network", None)
        od_matrix_factory = getattr(uow.repo, "get_od_matrix", None)
        transit_network = transit_network_factory() if callable(transit_network_factory) else None
        od_matrix = od_matrix_factory() if callable(od_matrix_factory) else None

        if not transit_network or not od_matrix:
            from src.domain.model.od_matrix import ODMatrix
            from src.domain.model.transit_network import TransitNetwork

            transit_network = TransitNetwork(stops, routes)
            od_matrix = ODMatrix(od_pairs, zones)

        od_routing_result_service = GenerateODRoutingResultService(
            routing_method=routing_engine,
            candidate_trip_filter=filter_engine,
        )
        od_routing_results = od_routing_result_service.generate_od_routing_result(
            od_matrix,
            transit_network,
            geometry_calculator,
        )
        trips = _collect_representative_trips(od_routing_results)

        results = []
        for index, trip in enumerate(trips, start=1):
            total_demand = None
            served_od_pairs = []

            for calculator in kpi_calculators:
                kpi_result = calculator.calculate(
                    trip,
                    transit_network,
                    od_matrix,
                    routing_engine,
                    geometry_calculator,
                )
                extracted_total_demand, extracted_served_od_pairs = (
                    _extract_total_potential_demand_result(kpi_result)
                )
                if extracted_total_demand is not None or extracted_served_od_pairs:
                    total_demand = extracted_total_demand
                    served_od_pairs = extracted_served_od_pairs

            results.append(
                {
                    "trip_id": f"Trip_{index}",
                    "summary": _build_trip_summary(total_demand),
                    "path": _build_trip_path(trip),
                    "served_od_pairs": served_od_pairs,
                }
            )

        return sorted(results, key=_trip_sort_key)
