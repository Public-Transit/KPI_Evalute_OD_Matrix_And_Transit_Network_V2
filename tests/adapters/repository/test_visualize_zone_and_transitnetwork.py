from __future__ import annotations

from contextlib import contextmanager, suppress
from pathlib import Path
import shutil
from uuid import uuid4

from src.adapters.repository.abstract_repository import AbstractRepository
from src.adapters.repository.visualize_zone_and_transitnetwork import (
    VisualizeZoneAndTransitNetwork,
)
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.model.point import Point
from src.domain.model.route import Route
from src.domain.model.stop import Stop
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.zone import Zone


def _build_loaded_data():
    stops = [
        Stop("S1", 1.0, 1.0),
        Stop("S2", 1.2, 1.2),
        Stop("S3", 2.0, 2.0),
        Stop("S4", 2.2, 2.2),
    ]
    routes = [
        Route("R1", [], ["S1", "S2", "S3"]),
        Route("R2", [Point(1.2, 1.2), Point(2.2, 2.2)], ["S2", "S4"]),
    ]
    zones = [
        Zone(
            "Z1",
            [Point(0.8, 0.8), Point(0.8, 1.3), Point(1.3, 1.3), Point(1.3, 0.8)],
            Point(1.05, 1.05),
        ),
        Zone(
            "Z2",
            [Point(1.7, 1.7), Point(1.7, 2.1), Point(2.1, 2.1), Point(2.1, 1.7)],
            Point(1.9, 1.9),
        ),
        Zone(
            "Z3",
            [Point(2.0, 2.0), Point(2.0, 2.4), Point(2.4, 2.4), Point(2.4, 2.0)],
            Point(2.2, 2.2),
        ),
    ]
    od_pairs = [
        ODPair("OD1", "Z1", "Z2", 50.0),
        ODPair("OD2", "Z2", "Z3", 20.0),
        ODPair("OD3", "Z1", "Z3", 80.0),
    ]
    return stops, routes, zones, od_pairs


class SpyRepository(AbstractRepository):
    def __init__(self):
        super().__init__()
        self.references = []
        self._loaded_data = _build_loaded_data()

    def get(self, reference):
        self.references.append(reference)
        return self._loaded_data


class RecordingVisualizer(VisualizeZoneAndTransitNetwork):
    def __init__(self):
        super().__init__()
        self.captured_od_pair_ids = {}

    def show_zones_and_routes(self, *args, **kwargs):
        return None

    def show_zones_and_od(self, od_matrix: ODMatrix, *args, **kwargs):
        self.captured_od_pair_ids["od"] = [
            od_pair.id() for od_pair in od_matrix.od_pairs()
        ]

    def show(self, od_matrix: ODMatrix, transit_network: TransitNetwork, *args, **kwargs):
        del transit_network
        self.captured_od_pair_ids["overview"] = [
            od_pair.id() for od_pair in od_matrix.od_pairs()
        ]


@contextmanager
def _output_dir():
    root_dir = Path("test_visualize_outputs")
    output_dir = root_dir / str(uuid4())
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield output_dir
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
        with suppress(OSError):
            root_dir.rmdir()


def test_show_repository_views_creates_three_output_files_and_calls_repo_once():
    repo = SpyRepository()
    visualizer = VisualizeZoneAndTransitNetwork()
    with _output_dir() as output_dir:
        output_paths = visualizer.show_repository_views(
            repo=repo,
            reference="demo-reference",
            save_dir=output_dir,
            file_prefix="demo",
            title_prefix="Demo",
            top_n_od_pairs=2,
            label_all_stops=True,
        )

        assert repo.references == ["demo-reference"]
        assert Path(output_paths["network"]).exists()
        assert Path(output_paths["od"]).exists()
        assert Path(output_paths["overview"]).exists()
        assert Path(output_paths["network"]).name == "demo_network.png"
        assert Path(output_paths["od"]).name == "demo_od_top2.png"
        assert Path(output_paths["overview"]).name == "demo_overview_top2.png"


def test_show_loaded_data_filters_top_n_od_pairs_and_can_render_all():
    stops, routes, zones, od_pairs = _build_loaded_data()
    visualizer = RecordingVisualizer()

    visualizer.show_loaded_data(
        stops=stops,
        routes=routes,
        zones=zones,
        od_pairs=od_pairs,
        save_dir=None,
        top_n_od_pairs=2,
    )

    assert visualizer.captured_od_pair_ids["od"] == ["OD3", "OD1"]
    assert visualizer.captured_od_pair_ids["overview"] == ["OD3", "OD1"]

    visualizer.show_loaded_data(
        stops=stops,
        routes=routes,
        zones=zones,
        od_pairs=od_pairs,
        save_dir=None,
        top_n_od_pairs=None,
    )

    assert visualizer.captured_od_pair_ids["od"] == ["OD1", "OD2", "OD3"]
    assert visualizer.captured_od_pair_ids["overview"] == ["OD1", "OD2", "OD3"]


def test_calculate_plot_layout_expands_narrow_axis_for_tall_network():
    stops, routes, zones, od_pairs = _build_loaded_data()
    visualizer = VisualizeZoneAndTransitNetwork()
    od_matrix = ODMatrix(od_pairs, zones)
    transit_network = TransitNetwork(stops, routes)

    x_limits, y_limits, figure_size = visualizer._calculate_plot_layout(
        od_matrix,
        transit_network,
    )

    span_x = x_limits[1] - x_limits[0]
    span_y = y_limits[1] - y_limits[0]
    assert max(span_x, span_y) / min(span_x, span_y) <= (
        visualizer.MAX_AXIS_ASPECT_RATIO + 0.25
    )
    assert figure_size[0] >= visualizer.MIN_FIGURE_WIDTH_IN
    assert figure_size[1] == visualizer.DEFAULT_FIGURE_HEIGHT_IN


def test_legacy_visualization_methods_still_save_images():
    stops, routes, zones, od_pairs = _build_loaded_data()
    visualizer = VisualizeZoneAndTransitNetwork()
    od_matrix = ODMatrix(od_pairs, zones)
    transit_network = TransitNetwork(stops, routes)
    with _output_dir() as output_dir:
        overview_path = output_dir / "overview.png"
        routes_path = output_dir / "routes.png"
        od_path = output_dir / "od.png"

        visualizer.show(
            od_matrix=od_matrix,
            transit_network=transit_network,
            save_path=overview_path,
            highlight_stop_ids=["S2"],
            buffer_radius_m=150,
        )
        visualizer.show_zones_and_routes(
            od_matrix=od_matrix,
            transit_network=transit_network,
            save_path=routes_path,
        )
        visualizer.show_zones_and_od(
            od_matrix=od_matrix,
            save_path=od_path,
        )

        assert overview_path.exists()
        assert routes_path.exists()
        assert od_path.exists()
