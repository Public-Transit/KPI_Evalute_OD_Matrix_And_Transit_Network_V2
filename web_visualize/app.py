from __future__ import annotations

import sys
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request

from flask import Flask, Response, jsonify, render_template, request

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator
from src.adapters.repository.cottbus_xml_repository import CottbusXmlRepository
from src.adapters.repository.siouxfalls_xml_repository import SiouxFallsXmlRepository
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.model.route import Route
from src.domain.model.stop import Stop
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.zone import Zone
from src.domain.service.aggregate.composite_quality_index import CompositeQualityIndexCalculator
from src.domain.service.aggregate.od_kpi_aggregator import ODKPIAggregator
from src.domain.service.filter import MinDistanceCandidateTripFilterV2
from src.domain.service.kpi_caculator.circuity_kpi import CircuityIndexCalculator
from src.domain.service.kpi_caculator.spatial_coverage_kpi import SpatialCoverageCalculator
from src.domain.service.kpi_caculator.transfer_kpi import TransferRateCalculator
from src.domain.service.routing import CombinedRoutingEngine
from src.service_layer.service import routing_services
from src.service_layer.unit_of_work import DummyUnitOfWork


APP = Flask(__name__, template_folder="templates", static_folder="static")
DEFAULT_DATASET = "siouxfalls"
DEFAULT_MAX_PLANS = 20
DEFAULT_GRID_CELL_SIZE_M = 500.0
DEFAULT_BACKEND_URL = "http://127.0.0.1:8000/api/kpi/calculate-all"


@APP.get("/")
def index() -> str:
    return render_template("index.html")


@APP.get("/health")
def health() -> Response:
    return jsonify({"status": "ok"})


@APP.get("/data/network")
def network_data() -> Response:
    dataset = request.args.get("dataset", DEFAULT_DATASET).strip().lower()
    max_plans = _parse_max_plans(request.args.get("max_plans"))
    grid_cell_size_m = _parse_positive_float(request.args.get("grid_cell_size_m"), DEFAULT_GRID_CELL_SIZE_M, field_name="grid_cell_size_m")
    top_n_od_pairs = _parse_optional_positive_int(request.args.get("top_n_od_pairs"))

    try:
        repo = _build_repository(dataset=dataset, max_plans=max_plans, grid_cell_size_m=grid_cell_size_m)
        stops, routes, zones, od_pairs = repo.get()
        return jsonify(_serialize_network(dataset=dataset, max_plans=max_plans, grid_cell_size_m=grid_cell_size_m, stops=stops, routes=routes, zones=zones, od_pairs=od_pairs, top_n_od_pairs=top_n_od_pairs))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@APP.post("/data/kpi/calculate-all")
def proxy_calculate_all() -> Response:
    payload = request.get_json(silent=True) or {}
    dataset = str(payload.get("dataset") or DEFAULT_DATASET).strip().lower()
    max_plans = _parse_max_plans(payload.get("max_plans"))
    grid_cell_size_m = _parse_positive_float(payload.get("grid_cell_size_m"), DEFAULT_GRID_CELL_SIZE_M, field_name="grid_cell_size_m")
    use_backend_proxy = bool(payload.get("use_backend_proxy", False))
    backend_url = str(payload.get("backend_url") or DEFAULT_BACKEND_URL).strip() or DEFAULT_BACKEND_URL

    try:
        if use_backend_proxy:
            return _proxy_backend_request(backend_url)
        return jsonify(_calculate_all_od_kpis(dataset=dataset, max_plans=max_plans, grid_cell_size_m=grid_cell_size_m))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


def _proxy_backend_request(backend_url: str) -> Response:
    try:
        proxy_request = urllib_request.Request(backend_url, method="POST", headers={"Accept": "application/json", "Content-Type": "application/json"}, data=b"{}")
        with urllib_request.urlopen(proxy_request, timeout=600) as response:
            response_body = response.read().decode("utf-8")
            return Response(response=response_body, status=response.status, mimetype="application/json")
    except urllib_error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        return jsonify({"error": "KPI backend returned an HTTP error", "backend_url": backend_url, "status_code": exc.code, "details": response_body}), exc.code
    except urllib_error.URLError as exc:
        return jsonify({"error": "Cannot reach KPI backend. Start FastAPI first and verify backend_url.", "backend_url": backend_url, "details": str(exc.reason)}), 502


def _build_repository(*, dataset: str, max_plans: int | None, grid_cell_size_m: float):
    if dataset == "siouxfalls":
        return SiouxFallsXmlRepository(data_dir="siouxfalls", max_plans=max_plans, grid_cell_size_m=grid_cell_size_m)
    if dataset == "cottbus":
        return CottbusXmlRepository(data_dir="cottbus", max_plans=max_plans, grid_cell_size_m=grid_cell_size_m)
    raise ValueError(f"Unsupported dataset: {dataset}")


def _parse_max_plans(raw_value) -> int | None:
    if raw_value is None:
        return DEFAULT_MAX_PLANS
    normalized = str(raw_value).strip()
    if not normalized:
        return DEFAULT_MAX_PLANS
    if normalized.lower() == "none":
        return None
    parsed = int(normalized)
    if parsed <= 0:
        raise ValueError("max_plans must be greater than 0 or None")
    return parsed


def _parse_positive_float(raw_value, default: float, *, field_name: str) -> float:
    if raw_value is None or not str(raw_value).strip():
        return default
    parsed = float(raw_value)
    if parsed <= 0:
        raise ValueError(f"{field_name} must be greater than 0")
    return parsed


def _parse_optional_positive_int(raw_value) -> int | None:
    if raw_value is None:
        return None
    normalized = str(raw_value).strip()
    if not normalized or normalized.lower() == "none":
        return None
    parsed = int(normalized)
    if parsed <= 0:
        raise ValueError("top_n_od_pairs must be greater than 0 or None")
    return parsed

def _serialize_network(*, dataset: str, max_plans: int | None, grid_cell_size_m: float, stops: list[Stop], routes: list[Route], zones: list[Zone], od_pairs: list[ODPair], top_n_od_pairs: int | None) -> dict:
    route_ids_by_stop_id: dict[str, set[str]] = {}
    for route in routes:
        for stop_id in route.stops_seq():
            route_ids_by_stop_id.setdefault(stop_id, set()).add(route.id())
    if top_n_od_pairs is not None:
        od_pairs = sorted(od_pairs, key=lambda od: od.demand(), reverse=True)[:top_n_od_pairs]
        selected_zone_ids = {od.origin_zone_id() for od in od_pairs} | {od.destination_zone_id() for od in od_pairs}
        zones = [zone for zone in zones if zone.id() in selected_zone_ids]
    serialized_stops = [{"id": stop.id(), "lat": stop.lat(), "lon": stop.lon(), "route_ids": sorted(route_ids_by_stop_id.get(stop.id(), set()))} for stop in stops]
    serialized_routes = [{"id": route.id(), "shape": [{"lat": point.lat(), "lon": point.lon()} for point in route.shape()], "stops_seq": route.stops_seq(), "start_stop_id": route.get_start_stop_id(), "end_stop_id": route.get_end_stop_id()} for route in routes]
    serialized_zones = [{"id": zone.id(), "centroid": {"lat": zone.centroid().lat(), "lon": zone.centroid().lon()}, "boundary": [{"lat": point.lat(), "lon": point.lon()} for point in zone.boundary()]} for zone in zones]
    serialized_od_pairs = [{"id": od_pair.id(), "origin_zone_id": od_pair.origin_zone_id(), "destination_zone_id": od_pair.destination_zone_id(), "demand": od_pair.demand()} for od_pair in od_pairs]
    return {"meta": {"dataset": dataset, "stop_count": len(serialized_stops), "route_count": len(serialized_routes), "zone_count": len(serialized_zones), "od_pair_count": len(serialized_od_pairs), "grid_cell_size_m": grid_cell_size_m, "max_plans": max_plans, "bbox": _calculate_bbox(serialized_stops, serialized_zones, serialized_routes)}, "stops": serialized_stops, "routes": serialized_routes, "zones": serialized_zones, "od_pairs": serialized_od_pairs}


def _calculate_bbox(serialized_stops: list[dict], serialized_zones: list[dict], serialized_routes: list[dict]) -> dict[str, float]:
    latitudes: list[float] = []
    longitudes: list[float] = []
    for stop in serialized_stops:
        latitudes.append(stop["lat"])
        longitudes.append(stop["lon"])
    for zone in serialized_zones:
        latitudes.append(zone["centroid"]["lat"])
        longitudes.append(zone["centroid"]["lon"])
        for point in zone["boundary"]:
            latitudes.append(point["lat"])
            longitudes.append(point["lon"])
    for route in serialized_routes:
        for point in route["shape"]:
            latitudes.append(point["lat"])
            longitudes.append(point["lon"])
    if not latitudes or not longitudes:
        return {"min_lat": 0.0, "max_lat": 1.0, "min_lon": 0.0, "max_lon": 1.0}
    return {"min_lat": min(latitudes), "max_lat": max(latitudes), "min_lon": min(longitudes), "max_lon": max(longitudes)}


def _calculate_all_od_kpis(*, dataset: str, max_plans: int | None, grid_cell_size_m: float) -> dict:
    repo = _build_repository(dataset=dataset, max_plans=max_plans, grid_cell_size_m=grid_cell_size_m)
    uow = DummyUnitOfWork(repo)
    routing_engine = CombinedRoutingEngine()
    filter_engine = MinDistanceCandidateTripFilterV2()
    geo_calc = ShapelyGeometryCalculator()
    results = routing_services.batch_route_all_od_pairs(routing_engine, filter_engine, uow, geo_calc, None)
    stops, routes, zones, od_pairs = repo.get()
    transit_network = TransitNetwork(stops, routes)
    od_matrix = ODMatrix(od_pairs, zones)
    transfer_calc = TransferRateCalculator()
    circuity_calc = CircuityIndexCalculator()
    spatial_calc = SpatialCoverageCalculator()
    composite_calc = CompositeQualityIndexCalculator()
    od_aggregator = ODKPIAggregator()
    json_results = []
    for routing_result in results:
        route_options_data = []
        trip_kpi_results = []
        for evaluated_option in routing_result.evaluated_routing_options():
            transfer_result = transfer_calc.calculate(evaluated_option)
            circuity_result = circuity_calc.calculate(evaluated_option, transit_network=transit_network, geometry_calculator=geo_calc)
            spatial_result = spatial_calc.calculate(evaluated_option, od_pair_id=routing_result.od_pair_id(), od_matrix=od_matrix, transit_network=transit_network, geometry_calculator=geo_calc)
            composite_result = composite_calc.calculate(transfer_result.get("score"), circuity_result.get("score"), spatial_result.get("score_ratio"))
            option_kpis = {"transfer_kpi": transfer_result, "circuity_kpi": circuity_result, "spatial_coverage_kpi": spatial_result, "composite_kpi": composite_result}
            trip_kpi_results.append(option_kpis)
            route_options_data.append({"path": _build_path_payload(evaluated_option), "metrics": {"composite_score": _coerce_metric_value(composite_result.get("score")), "transfer_count": _coerce_transfer_count(transfer_result.get("score")), "circuity_index": _coerce_metric_value(circuity_result.get("score")), "coverage_ratio": _coerce_metric_value(spatial_result.get("score_ratio"))}})
        aggregated_kpis = od_aggregator.calculate(trip_kpi_results)
        json_results.append({"od_pair_id": routing_result.od_pair_id(), "summary": _build_summary(aggregated_kpis), "route_options": _sort_and_number_route_options(route_options_data)})
    return {"status": "success", "data": json_results}


def _coerce_metric_value(value):
    if isinstance(value, bool):
        return None
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _coerce_transfer_count(value):
    numeric = _coerce_metric_value(value)
    if numeric is None:
        return None
    return int(numeric) if float(numeric).is_integer() else None


def _build_summary(aggregated_kpis: dict) -> dict:
    composite_kpi = aggregated_kpis["composite_kpi"]
    return {"is_valid": composite_kpi["is_valid"], "reason": composite_kpi["reason"], "scores": {"composite": aggregated_kpis["composite_kpi"]["score"], "transfer": aggregated_kpis["transfer_kpi"]["score"], "circuity": aggregated_kpis["circuity_kpi"]["score"], "spatial_coverage": aggregated_kpis["spatial_coverage_kpi"]["score"]}}


def _build_path_payload(evaluated_option) -> dict:
    representative_trip = evaluated_option.representative_trip()
    if not representative_trip or not representative_trip.legs:
        return {"route_sequence": [], "stop_sequence": []}
    return {"route_sequence": [leg.route_id for leg in representative_trip.legs], "stop_sequence": [leg.board_stop_id for leg in representative_trip.legs] + [representative_trip.legs[-1].alight_stop_id]}


def _sort_and_number_route_options(route_options: list[dict]) -> list[dict]:
    sorted_options = sorted(route_options, key=lambda option: (option["metrics"]["composite_score"] is None, -(option["metrics"]["composite_score"] or 0.0)))
    return [{"option_id": f"OPT{index}", "path": option["path"], "metrics": option["metrics"]} for index, option in enumerate(sorted_options, start=1)]


if __name__ == "__main__":
    APP.run(host="127.0.0.1", port=5001, debug=True)
