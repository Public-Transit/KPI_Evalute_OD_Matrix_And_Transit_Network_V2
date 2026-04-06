from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from src.adapters.repository.abstract_repository import AbstractRepository
from src.domain.model.od_pair import ODPair
from src.domain.model.point import Point
from src.domain.model.route import Route
from src.domain.model.stop import Stop
from src.domain.model.zone import Zone


class CottbusXmlRepository(AbstractRepository):
    """
    Simple XML repository for PoC usage.

    It converts MATSim x/y to lat/lon so geodesic utilities can work safely:
    - lon = x / 10000
    - lat = y / 100000
    """

    def __init__(
        self,
        data_dir: str | Path = "cottbus",
        schedule_file: str = "schedule.xml",
        plans_file: str = "plans_scale0.375true.xml",
        max_plans: int = 200,
        zone_half_size_deg: float = 0.01,
        default_demand: float = 1.0,
    ):
        if max_plans <= 0:
            raise ValueError("max_plans must be greater than 0")
        if zone_half_size_deg <= 0:
            raise ValueError("zone_half_size_deg must be greater than 0")

        self._data_dir = Path(data_dir)
        self._schedule_file = schedule_file
        self._plans_file = plans_file
        self._max_plans = max_plans
        self._zone_half_size_deg = zone_half_size_deg
        self._default_demand = default_demand

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

    @staticmethod
    def _to_lat_lon(x_m: float, y_m: float) -> tuple[float, float]:
        lon = x_m / 10000.0
        lat = y_m / 100000.0
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
        zones: list[Zone] = []
        od_pairs: list[ODPair] = []
        zone_id_counter = 1

        for person in root.findall(".//person"):
            if len(od_pairs) >= self._max_plans:
                break

            selected_plan = person.find("./plan[@selected='yes']")
            if selected_plan is None:
                selected_plan = person.find("./plan")
            if selected_plan is None:
                continue

            acts = selected_plan.findall("act")
            if len(acts) < 2:
                continue

            origin_point = self._extract_point(acts[0])
            destination_point = self._extract_point(acts[1])
            if origin_point is None or destination_point is None:
                continue

            zone_origin = self._build_square_zone(f"Z{zone_id_counter}", origin_point)
            zone_id_counter += 1
            zone_destination = self._build_square_zone(
                f"Z{zone_id_counter}", destination_point
            )
            zone_id_counter += 1

            zones.extend([zone_origin, zone_destination])

            person_id = person.get("id") or str(len(od_pairs) + 1)
            od_pairs.append(
                ODPair(
                    od_pair_id=f"OD_{person_id}",
                    origin_zone_id=zone_origin.id(),
                    destination_zone_id=zone_destination.id(),
                    demand=self._default_demand,
                )
            )

        return zones, od_pairs

    def _extract_point(self, act_elem) -> Point | None:
        x_raw = act_elem.get("x")
        y_raw = act_elem.get("y")
        if x_raw is None or y_raw is None:
            return None

        try:
            x_m = float(x_raw)
            y_m = float(y_raw)
        except ValueError:
            return None

        lat, lon = self._to_lat_lon(x_m, y_m)
        return Point(lat, lon)

    def _build_square_zone(self, zone_id: str, centroid: Point) -> Zone:
        half = self._zone_half_size_deg
        lat = centroid.lat()
        lon = centroid.lon()
        boundary = [
            Point(lat - half, lon - half),
            Point(lat - half, lon + half),
            Point(lat + half, lon + half),
            Point(lat + half, lon - half),
        ]
        return Zone(zone_id, boundary, centroid)
