from __future__ import annotations

from contextlib import contextmanager, suppress
from pathlib import Path
import shutil
from uuid import uuid4

from src.adapters.repository.cottbus_xml_repository import CottbusXmlRepository
from src.adapters.repository.siouxfalls_xml_repository import SiouxFallsXmlRepository


@contextmanager
def _xml_fixture_dir():
    root_dir = Path("test_xml_repository_data")
    fixture_dir = root_dir / str(uuid4())
    fixture_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield fixture_dir
    finally:
        shutil.rmtree(fixture_dir, ignore_errors=True)
        with suppress(OSError):
            root_dir.rmdir()


def test_cottbus_transform_projects_coordinates_to_cottbus_bbox():
    repo = CottbusXmlRepository(max_plans=3)

    lat, lon = repo._to_lat_lon(455551.5822241595, 5728935.910032587)

    assert 51.0 < lat < 53.0
    assert 13.0 < lon < 15.0


def test_siouxfalls_transform_projects_coordinates_to_siouxfalls_bbox():
    repo = SiouxFallsXmlRepository(max_plans=3)

    lat, lon = repo._to_lat_lon(682947.637268434, 4825919.285100707)

    assert 43.0 < lat < 44.5
    assert -97.5 < lon < -96.0


def test_cottbus_get_uses_grid_zoning_with_real_xml():
    repo = CottbusXmlRepository(max_plans=3)

    stops, routes, zones, od_pairs = repo.get()

    assert len(stops) > 100
    assert len(routes) > 0
    assert 1 <= len(zones) <= 6
    assert 1 <= len(od_pairs) <= 3
    assert all(zone.id().startswith("G_") for zone in zones)
    assert all(od_pair.id().startswith("OD_G_") for od_pair in od_pairs)
    assert 51.0 < stops[0].lat() < 53.0
    assert 13.0 < stops[0].lon() < 15.0


def test_siouxfalls_get_uses_grid_zoning_with_real_xml():
    repo = SiouxFallsXmlRepository(max_plans=3)

    stops, routes, zones, od_pairs = repo.get()

    assert len(stops) > 50
    assert len(routes) > 0
    assert 1 <= len(zones) <= 6
    assert 1 <= len(od_pairs) <= 3
    assert all(zone.id().startswith("G_") for zone in zones)
    assert all(od_pair.id().startswith("OD_G_") for od_pair in od_pairs)
    assert 43.0 < stops[0].lat() < 44.5
    assert -97.5 < stops[0].lon() < -96.0


def test_grid_zoning_reuses_cells_and_aggregates_demand_for_cottbus_repository():
    with _xml_fixture_dir() as fixture_dir:
        schedule_path = fixture_dir / "schedule.xml"
        plans_path = fixture_dir / "plans.xml"

        schedule_path.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<transitSchedule>
  <transitStops>
    <stopFacility id="S1" x="455100" y="5728100" />
    <stopFacility id="S2" x="456100" y="5729100" />
  </transitStops>
  <transitLine id="L1">
    <transitRoute id="R1">
      <routeProfile>
        <stop refId="S1" />
        <stop refId="S2" />
      </routeProfile>
    </transitRoute>
  </transitLine>
</transitSchedule>
""",
            encoding="utf-8",
        )
        plans_path.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<population>
  <person id="P1">
    <plan selected="yes">
      <act type="home" x="455100" y="5728100" />
      <act type="work" x="456100" y="5729100" />
    </plan>
  </person>
  <person id="P2">
    <plan selected="yes">
      <act type="home" x="455300" y="5728300" />
      <act type="work" x="456400" y="5729400" />
    </plan>
  </person>
  <person id="P3">
    <plan selected="yes">
      <act type="home" x="457100" y="5730100" />
      <act type="work" x="458100" y="5731100" />
    </plan>
  </person>
</population>
""",
            encoding="utf-8",
        )

        repo = CottbusXmlRepository(
            data_dir=fixture_dir,
            plans_file="plans.xml",
            max_plans=3,
            grid_cell_size_m=500.0,
        )

        stops, routes, zones, od_pairs = repo.get()

        assert len(stops) == 2
        assert len(routes) == 1
        assert len(zones) == 4
        assert len(od_pairs) == 2
        assert any(od_pair.demand() == 2.0 for od_pair in od_pairs)
        assert {zone.id() for zone in zones} == {
            "G_910_11456",
            "G_912_11458",
            "G_914_11460",
            "G_916_11462",
        }
        for zone in zones:
            assert len(zone.boundary()) == 4


def test_grid_zone_boundary_is_built_from_projected_cell_corners():
    repo = CottbusXmlRepository(max_plans=1, grid_cell_size_m=500.0)

    zone = repo._build_grid_zone("G_910_11456", 910, 11456)

    assert zone.id() == "G_910_11456"
    assert len(zone.boundary()) == 4
    assert 51.0 < zone.centroid().lat() < 53.0
    assert 13.0 < zone.centroid().lon() < 15.0
    latitudes = [point.lat() for point in zone.boundary()]
    longitudes = [point.lon() for point in zone.boundary()]
    assert min(latitudes) < zone.centroid().lat() < max(latitudes)
    assert min(longitudes) < zone.centroid().lon() < max(longitudes)


def test_max_plans_none_loads_all_valid_persons():
    with _xml_fixture_dir() as fixture_dir:
        schedule_path = fixture_dir / "schedule.xml"
        plans_path = fixture_dir / "plans.xml"

        schedule_path.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<transitSchedule>
  <transitStops>
    <stopFacility id="S1" x="455100" y="5728100" />
    <stopFacility id="S2" x="456100" y="5729100" />
  </transitStops>
  <transitLine id="L1">
    <transitRoute id="R1">
      <routeProfile>
        <stop refId="S1" />
        <stop refId="S2" />
      </routeProfile>
    </transitRoute>
  </transitLine>
</transitSchedule>
""",
            encoding="utf-8",
        )
        plans_path.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<population>
  <person id="P1">
    <plan selected="yes">
      <act type="home" x="455100" y="5728100" />
      <act type="work" x="456100" y="5729100" />
    </plan>
  </person>
  <person id="P2">
    <plan selected="yes">
      <act type="home" x="455300" y="5728300" />
      <act type="work" x="456400" y="5729400" />
    </plan>
  </person>
  <person id="P3">
    <plan selected="yes">
      <act type="home" x="457100" y="5730100" />
      <act type="work" x="458100" y="5731100" />
    </plan>
  </person>
</population>
""",
            encoding="utf-8",
        )

        repo = CottbusXmlRepository(
            data_dir=fixture_dir,
            plans_file="plans.xml",
            max_plans=None,
            grid_cell_size_m=500.0,
        )

        _, _, zones, od_pairs = repo.get()

        assert len(zones) == 4
        assert len(od_pairs) == 2
        assert sorted(od_pair.demand() for od_pair in od_pairs) == [1.0, 2.0]
