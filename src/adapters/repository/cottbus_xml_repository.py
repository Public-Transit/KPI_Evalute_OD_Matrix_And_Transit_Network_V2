from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

from pyproj import Transformer

from src.adapters.repository.abstract_repository import AbstractRepository
from src.domain.model.od_pair import ODPair
from src.domain.model.point import Point
from src.domain.model.route import Route
from src.domain.model.stop import Stop
from src.domain.model.zone import Zone


class CottbusXmlRepository(AbstractRepository):
    """
    XML repository for MATSim inputs with projected coordinates.

    Coordinates are transformed from a dataset-specific projected CRS into
    WGS84 (lat/lon) so geodesic calculations can work correctly across the
    rest of the system. Demand zones are generated from shared projected
    grid cells instead of per-person square buffers.
    """

    def __init__(
        self,
        data_dir: str | Path = "data/input/cottbus",
        schedule_file: str = "schedule.xml",
        plans_file: str = "plans_scale0.375true.xml",
        max_plans: int | None = 200,
        grid_cell_size_m: float = 500.0,
        default_demand: float = 1.0,
        source_crs: str = "EPSG:32633",
        target_crs: str = "EPSG:4326",
    ):
        if max_plans is not None and max_plans <= 0:
            raise ValueError("max_plans must be greater than 0 or None")
        if grid_cell_size_m <= 0:
            raise ValueError("grid_cell_size_m must be greater than 0")
        if not source_crs:
            raise ValueError("source_crs must not be empty")
        if not target_crs:
            raise ValueError("target_crs must not be empty")

        self._data_dir = Path(data_dir)
        self._schedule_file = schedule_file
        self._plans_file = plans_file
        self._max_plans = max_plans
        self._grid_cell_size_m = grid_cell_size_m
        self._default_demand = default_demand
        self._source_crs = source_crs
        self._target_crs = target_crs
        self._coordinate_transformer = Transformer.from_crs(
            self._source_crs,
            self._target_crs,
            always_xy=True,
        )

    def get(
        self,
        reference=None,
    ) -> tuple[list[Stop], list[Route], list[Zone], list[ODPair]]:
        schedule_path, plans_path = self._resolve_input_paths(reference)
        stops = self._parse_stops(schedule_path)
        routes = self._parse_routes(schedule_path, stops)
        zones, od_pairs = self._parse_zones_and_od_pairs(plans_path)
        return stops, routes, zones, od_pairs

    def _resolve_input_paths(self, reference) -> tuple[Path, Path]:
        base_dir = Path(reference) if reference else self._data_dir
        schedule_path = base_dir / self._schedule_file
        plans_path = base_dir / self._plans_file

        if not schedule_path.exists():
            raise FileNotFoundError(f"Schedule file does not exist: {schedule_path}")
        if not plans_path.exists():
            raise FileNotFoundError(f"Plans file does not exist: {plans_path}")

        return schedule_path, plans_path

    def _to_lat_lon(self, x_m: float, y_m: float) -> tuple[float, float]:
        lon, lat = self._coordinate_transformer.transform(x_m, y_m)
        return lat, lon

    def _parse_stops(self, schedule_path: Path) -> list[Stop]:
        root = ET.parse(schedule_path).getroot()
        stops: list[Stop] = []

        for stop_elem in root.findall("./transitStops/stopFacility"):
            stop_id = stop_elem.get("id")
            x_raw = stop_elem.get("x")
            y_raw = stop_elem.get("y")
            if not stop_id or x_raw is None or y_raw is None:
                continue

            try:
                x_m = float(x_raw)
                y_m = float(y_raw)
            except ValueError:
                continue

            lat, lon = self._to_lat_lon(x_m, y_m)
            stops.append(Stop(stop_id, lat, lon))

        return stops

    def _parse_routes(self, schedule_path: Path, stops: list[Stop]) -> list[Route]:
        root = ET.parse(schedule_path).getroot()
        stop_map = {stop.id(): stop for stop in stops}
        routes: list[Route] = []

        for line_elem in root.findall("./transitLine"):
            line_id = line_elem.get("id")
            if not line_id:
                continue

            for route_elem in line_elem.findall("./transitRoute"):
                route_id = route_elem.get("id")
                if not route_id:
                    continue

                stop_ids: list[str] = []
                for profile_stop in route_elem.findall("./routeProfile/stop"):
                    stop_id = profile_stop.get("refId")
                    if stop_id and stop_id in stop_map:
                        stop_ids.append(stop_id)

                if len(stop_ids) < 2:
                    continue

                shape = [stop_map[stop_id].coord() for stop_id in stop_ids]
                routes.append(Route(f"{line_id}_{route_id}", shape, stop_ids))

        return routes

    def _parse_zones_and_od_pairs(self, plans_path: Path) -> tuple[list[Zone], list[ODPair]]:
        root = ET.parse(plans_path).getroot()
        zone_map: dict[str, Zone] = {}
        od_demand_map: dict[tuple[str, str], float] = {}
        processed_plans = 0

        for person in root.findall(".//person"):
            if self._max_plans is not None and processed_plans >= self._max_plans:
                break

            selected_plan = person.find("./plan[@selected='yes']")
            if selected_plan is None:
                selected_plan = person.find("./plan")
            if selected_plan is None:
                continue

            acts = selected_plan.findall("act")
            if len(acts) < 2:
                continue

            origin_xy = self._extract_projected_xy(acts[0])
            destination_xy = self._extract_projected_xy(acts[1])
            if origin_xy is None or destination_xy is None:
                continue

            processed_plans += 1

            origin_col, origin_row = self._grid_indices(*origin_xy)
            destination_col, destination_row = self._grid_indices(*destination_xy)
            origin_cell_id = self._build_cell_id(origin_col, origin_row)
            destination_cell_id = self._build_cell_id(destination_col, destination_row)

            zone_map.setdefault(
                origin_cell_id,
                self._build_grid_zone(origin_cell_id, origin_col, origin_row),
            )
            zone_map.setdefault(
                destination_cell_id,
                self._build_grid_zone(
                    destination_cell_id,
                    destination_col,
                    destination_row,
                ),
            )

            od_key = (origin_cell_id, destination_cell_id)
            od_demand_map[od_key] = od_demand_map.get(od_key, 0.0) + self._default_demand

        od_pairs = [
            ODPair(
                od_pair_id=self._build_od_pair_id(origin_zone_id, destination_zone_id),
                origin_zone_id=origin_zone_id,
                destination_zone_id=destination_zone_id,
                demand=demand,
            )
            for (origin_zone_id, destination_zone_id), demand in od_demand_map.items()
        ]
        return list(zone_map.values()), od_pairs

    def _extract_projected_xy(self, act_elem) -> tuple[float, float] | None:
        x_raw = act_elem.get("x")
        y_raw = act_elem.get("y")
        if x_raw is None or y_raw is None:
            return None

        try:
            x_m = float(x_raw)
            y_m = float(y_raw)
        except ValueError:
            return None

        return x_m, y_m

    def _projected_to_point(self, x_m: float, y_m: float) -> Point:
        lat, lon = self._to_lat_lon(x_m, y_m)
        return Point(lat, lon)

    def _grid_indices(self, x_m: float, y_m: float) -> tuple[int, int]:
        return (
            math.floor(x_m / self._grid_cell_size_m),
            math.floor(y_m / self._grid_cell_size_m),
        )

    def _build_cell_id(self, col: int, row: int) -> str:
        return f"G_{col}_{row}"

    def _build_od_pair_id(self, origin_zone_id: str, destination_zone_id: str) -> str:
        return f"OD_{origin_zone_id}__{destination_zone_id}"

    def _build_grid_zone(self, zone_id: str, col: int, row: int) -> Zone:
        min_x = col * self._grid_cell_size_m
        min_y = row * self._grid_cell_size_m
        max_x = min_x + self._grid_cell_size_m
        max_y = min_y + self._grid_cell_size_m

        boundary = [
            self._projected_to_point(min_x, min_y),
            self._projected_to_point(min_x, max_y),
            self._projected_to_point(max_x, max_y),
            self._projected_to_point(max_x, min_y),
        ]
        centroid = self._projected_to_point(
            min_x + self._grid_cell_size_m / 2,
            min_y + self._grid_cell_size_m / 2,
        )
        return Zone(zone_id, boundary, centroid)
