from __future__ import annotations

import math
from pathlib import Path

import matplotlib
import matplotlib.patches as patches

from src.adapters.repository.abstract_repository import AbstractRepository
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.model.route import Route
from src.domain.model.stop import Stop
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.zone import Zone


matplotlib.use("Agg")
import matplotlib.pyplot as plt


class VisualizeZoneAndTransitNetwork:
    DEFAULT_TOP_N_OD_PAIRS = 20
    DEFAULT_FIGURE_HEIGHT_IN = 18.0
    MIN_FIGURE_WIDTH_IN = 14.0
    MAX_FIGURE_WIDTH_IN = 24.0
    MIN_AXIS_SPAN = 0.001
    AXIS_PADDING_RATIO = 0.08
    MIN_AXIS_PADDING = 0.0005
    MAX_AXIS_ASPECT_RATIO = 2.5
    SAVE_DPI = 300
    ZONE_COLORS = [
        "#ff9999",
        "#99ff99",
        "#9999ff",
        "#ffff99",
        "#ffcc99",
        "#cc99ff",
        "#99ffff",
        "#ffb3e6",
        "#c2c2f0",
    ]
    ROUTE_COLORS = [
        "#e6194b",
        "#3cb44b",
        "#ffe119",
        "#4363d8",
        "#f58231",
        "#911eb4",
        "#46f0f0",
    ]

    def show_repository_views(
        self,
        repo: AbstractRepository,
        reference=None,
        save_dir: str | Path = "data/output/plot_results",
        file_prefix: str = "repo",
        title_prefix: str | None = None,
        top_n_od_pairs: int | None = DEFAULT_TOP_N_OD_PAIRS,
        highlight_stop_ids: list[str] | None = None,
        buffer_radius_m: float | None = None,
        label_all_stops: bool = False,
    ) -> dict[str, str | None]:
        stops, routes, zones, od_pairs = repo.get(reference)
        return self.show_loaded_data(
            stops=stops,
            routes=routes,
            zones=zones,
            od_pairs=od_pairs,
            save_dir=save_dir,
            file_prefix=file_prefix,
            title_prefix=title_prefix,
            top_n_od_pairs=top_n_od_pairs,
            highlight_stop_ids=highlight_stop_ids,
            buffer_radius_m=buffer_radius_m,
            label_all_stops=label_all_stops,
        )

    def show_loaded_data(
        self,
        stops: list[Stop],
        routes: list[Route],
        zones: list[Zone],
        od_pairs: list[ODPair],
        save_dir: str | Path = "data/output/plot_results",
        file_prefix: str = "repo",
        title_prefix: str | None = None,
        top_n_od_pairs: int | None = DEFAULT_TOP_N_OD_PAIRS,
        highlight_stop_ids: list[str] | None = None,
        buffer_radius_m: float | None = None,
        label_all_stops: bool = False,
    ) -> dict[str, str | None]:
        transit_network, od_matrix = self._build_models(stops, routes, zones, od_pairs)
        return self.show_network_views(
            od_matrix=od_matrix,
            transit_network=transit_network,
            save_dir=save_dir,
            file_prefix=file_prefix,
            title_prefix=title_prefix,
            top_n_od_pairs=top_n_od_pairs,
            highlight_stop_ids=highlight_stop_ids,
            buffer_radius_m=buffer_radius_m,
            label_all_stops=label_all_stops,
        )

    def show_network_views(
        self,
        od_matrix: ODMatrix,
        transit_network: TransitNetwork,
        save_dir: str | Path = "data/output/plot_results",
        file_prefix: str = "repo",
        title_prefix: str | None = None,
        top_n_od_pairs: int | None = DEFAULT_TOP_N_OD_PAIRS,
        highlight_stop_ids: list[str] | None = None,
        buffer_radius_m: float | None = None,
        label_all_stops: bool = False,
    ) -> dict[str, str | None]:
        filtered_od_matrix = self._filter_od_matrix(od_matrix, top_n_od_pairs)
        output_paths = self._build_output_paths(save_dir, file_prefix, top_n_od_pairs)
        title_prefix = title_prefix or file_prefix

        self.show_zones_and_routes(
            od_matrix=od_matrix,
            transit_network=transit_network,
            save_path=output_paths["network"],
            title=f"{title_prefix} - Network",
            label_all_stops=label_all_stops,
            highlight_stop_ids=highlight_stop_ids,
        )
        self.show_zones_and_od(
            od_matrix=filtered_od_matrix,
            save_path=output_paths["od"],
            title=f"{title_prefix} - OD Demand",
            total_od_count=len(od_matrix.od_pairs()),
        )
        self.show(
            od_matrix=filtered_od_matrix,
            transit_network=transit_network,
            save_path=output_paths["overview"],
            title=f"{title_prefix} - Overview",
            highlight_stop_ids=highlight_stop_ids,
            buffer_radius_m=buffer_radius_m,
            label_all_stops=label_all_stops,
            total_od_count=len(od_matrix.od_pairs()),
        )
        return output_paths

    def show(
        self,
        od_matrix: ODMatrix,
        transit_network: TransitNetwork,
        save_path=None,
        title=None,
        highlight_stop_ids=None,
        buffer_radius_m=None,
        label_all_stops: bool = False,
        total_od_count: int | None = None,
    ):
        fig, ax = self._create_figure_and_axes(od_matrix, transit_network)

        self._draw_zones(
            ax,
            od_matrix,
            alpha=0.35,
            show_centroids=True,
            show_corner_labels=True,
        )
        self._draw_routes(
            ax,
            transit_network,
            linewidth=3.5,
            alpha=0.8,
            show_markers=False,
            show_mid_labels=False,
        )
        self._draw_stops(
            ax,
            transit_network,
            scatter_size=18,
            label_fontsize=7,
            x_offset=0.00005,
            y_offset=-0.0001,
            show_labels=label_all_stops,
            label_stop_ids=set(highlight_stop_ids or []),
        )
        self._draw_highlighted_stops(
            ax,
            transit_network,
            highlight_stop_ids or [],
            buffer_radius_m,
        )
        self._draw_od_pairs(ax, od_matrix)
        self._apply_common_layout(
            fig,
            ax,
            title or "Transit Network Overview",
            footer_text=self._build_od_footer_text(
                od_matrix,
                total_od_count=total_od_count,
            ),
            footer_rect=[0, 0.12, 1, 1],
            legend_title="Legend",
        )
        self._save_or_show(fig, save_path)

    def show_zones_and_routes(
        self,
        od_matrix: ODMatrix,
        transit_network: TransitNetwork,
        save_path=None,
        title=None,
        label_all_stops: bool = False,
        highlight_stop_ids: list[str] | None = None,
    ):
        fig, ax = self._create_figure_and_axes(od_matrix, transit_network)

        self._draw_zones(
            ax,
            od_matrix,
            alpha=0.3,
            show_centroids=True,
            show_corner_labels=True,
        )
        self._draw_routes(
            ax,
            transit_network,
            linewidth=4,
            alpha=0.7,
            show_markers=False,
            show_mid_labels=True,
        )
        self._draw_stops(
            ax,
            transit_network,
            scatter_size=15,
            label_fontsize=7,
            y_offset=-0.00015,
            show_labels=label_all_stops,
            label_stop_ids=set(highlight_stop_ids or []),
        )
        self._draw_highlighted_stops(
            ax,
            transit_network,
            highlight_stop_ids or [],
            buffer_radius_m=None,
        )
        self._apply_common_layout(
            fig,
            ax,
            title or "Transit Network Routes and Stops",
            footer_text=self._build_route_footer_text(transit_network),
            footer_box_color="lightgrey",
            footer_rect=[0, 0.12, 1, 1],
            legend_title="Legend",
        )
        self._save_or_show(fig, save_path)

    def show_zones_and_od(
        self,
        od_matrix: ODMatrix,
        save_path=None,
        title=None,
        total_od_count: int | None = None,
    ):
        fig, ax = self._create_figure_and_axes(od_matrix)

        self._draw_zones(
            ax,
            od_matrix,
            alpha=0.35,
            show_centroids=True,
            show_corner_labels=True,
        )
        self._draw_od_pairs(ax, od_matrix)
        self._apply_common_layout(
            fig,
            ax,
            title or "OD Demand Map",
            footer_text=self._build_od_footer_text(
                od_matrix,
                total_od_count=total_od_count,
            ),
            footer_rect=[0, 0.12, 1, 1],
            legend_title="Zones",
        )
        self._save_or_show(fig, save_path)

    def _build_models(
        self,
        stops: list[Stop],
        routes: list[Route],
        zones: list[Zone],
        od_pairs: list[ODPair],
    ) -> tuple[TransitNetwork, ODMatrix]:
        return TransitNetwork(stops, routes), ODMatrix(od_pairs, zones)

    def _create_figure_and_axes(
        self,
        od_matrix: ODMatrix,
        transit_network: TransitNetwork | None = None,
    ):
        x_limits, y_limits, figure_size = self._calculate_plot_layout(
            od_matrix,
            transit_network,
        )
        fig, ax = plt.subplots(figsize=figure_size)
        ax.set_xlim(*x_limits)
        ax.set_ylim(*y_limits)
        return fig, ax

    def _calculate_plot_layout(
        self,
        od_matrix: ODMatrix,
        transit_network: TransitNetwork | None = None,
    ) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        x_values, y_values = self._collect_plot_coordinates(od_matrix, transit_network)
        min_x = min(x_values)
        max_x = max(x_values)
        min_y = min(y_values)
        max_y = max(y_values)

        span_x = max(max_x - min_x, self.MIN_AXIS_SPAN)
        span_y = max(max_y - min_y, self.MIN_AXIS_SPAN)
        span_x, span_y = self._expand_short_axis(span_x, span_y)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        padding_x = max(span_x * self.AXIS_PADDING_RATIO, self.MIN_AXIS_PADDING)
        padding_y = max(span_y * self.AXIS_PADDING_RATIO, self.MIN_AXIS_PADDING)

        x_limits = (
            center_x - span_x / 2 - padding_x,
            center_x + span_x / 2 + padding_x,
        )
        y_limits = (
            center_y - span_y / 2 - padding_y,
            center_y + span_y / 2 + padding_y,
        )
        figure_size = self._build_figure_size(x_limits, y_limits)
        return x_limits, y_limits, figure_size

    def _collect_plot_coordinates(
        self,
        od_matrix: ODMatrix,
        transit_network: TransitNetwork | None = None,
    ) -> tuple[list[float], list[float]]:
        x_values: list[float] = []
        y_values: list[float] = []

        for zone in od_matrix.zones():
            for point in zone.boundary():
                x_values.append(point.lat())
                y_values.append(point.lon())
            x_values.append(zone.centroid().lat())
            y_values.append(zone.centroid().lon())

        if transit_network:
            for stop in transit_network.stops():
                x_values.append(stop.coord().lat())
                y_values.append(stop.coord().lon())

            for route in transit_network.routes():
                for point in self._resolve_route_shape(route, transit_network):
                    x_values.append(point.lat())
                    y_values.append(point.lon())

        if not x_values or not y_values:
            return [0.0, 1.0], [0.0, 1.0]
        return x_values, y_values

    def _expand_short_axis(
        self,
        span_x: float,
        span_y: float,
    ) -> tuple[float, float]:
        long_span = max(span_x, span_y)
        target_short_span = max(long_span / self.MAX_AXIS_ASPECT_RATIO, self.MIN_AXIS_SPAN)

        if span_x < span_y:
            span_x = max(span_x, target_short_span)
        elif span_y < span_x:
            span_y = max(span_y, target_short_span)

        return span_x, span_y

    def _build_figure_size(
        self,
        x_limits: tuple[float, float],
        y_limits: tuple[float, float],
    ) -> tuple[float, float]:
        span_x = x_limits[1] - x_limits[0]
        span_y = y_limits[1] - y_limits[0]
        aspect_ratio = max(span_x / max(span_y, self.MIN_AXIS_SPAN), 0.1)
        figure_height = self.DEFAULT_FIGURE_HEIGHT_IN
        figure_width = min(
            max(figure_height * aspect_ratio, self.MIN_FIGURE_WIDTH_IN),
            self.MAX_FIGURE_WIDTH_IN,
        )
        return figure_width, figure_height

    def _build_output_paths(
        self,
        save_dir: str | Path | None,
        file_prefix: str,
        top_n_od_pairs: int | None,
    ) -> dict[str, str | None]:
        if save_dir is None:
            return {"network": None, "od": None, "overview": None}

        save_dir_path = Path(save_dir)
        save_dir_path.mkdir(parents=True, exist_ok=True)
        od_suffix = self._build_od_suffix(top_n_od_pairs)
        return {
            "network": str(save_dir_path / f"{file_prefix}_network.png"),
            "od": str(save_dir_path / f"{file_prefix}_od_{od_suffix}.png"),
            "overview": str(save_dir_path / f"{file_prefix}_overview_{od_suffix}.png"),
        }

    def _build_od_suffix(self, top_n_od_pairs: int | None) -> str:
        if top_n_od_pairs is None:
            return "all"
        return f"top{top_n_od_pairs}"

    def _filter_od_matrix(
        self,
        od_matrix: ODMatrix,
        top_n_od_pairs: int | None,
    ) -> ODMatrix:
        if top_n_od_pairs is None:
            return od_matrix
        if top_n_od_pairs <= 0:
            raise ValueError("top_n_od_pairs must be greater than 0 or None")

        selected_od_pairs = sorted(
            od_matrix.od_pairs(),
            key=lambda od_pair: od_pair.demand(),
            reverse=True,
        )[:top_n_od_pairs]
        selected_zone_ids = {
            od_pair.origin_zone_id() for od_pair in selected_od_pairs
        } | {
            od_pair.destination_zone_id() for od_pair in selected_od_pairs
        }
        selected_zones = [
            zone for zone in od_matrix.zones() if zone.id() in selected_zone_ids
        ]
        return ODMatrix(selected_od_pairs, selected_zones)

    def _draw_zones(
        self,
        ax,
        od_matrix: ODMatrix,
        *,
        alpha: float,
        show_centroids: bool,
        show_corner_labels: bool,
    ) -> None:
        for index, zone in enumerate(od_matrix.zones()):
            boundary = zone.boundary()
            xs = [point.lat() for point in boundary]
            ys = [point.lon() for point in boundary]

            polygon = patches.Polygon(
                xy=list(zip(xs, ys)),
                closed=True,
                facecolor=self.ZONE_COLORS[index % len(self.ZONE_COLORS)],
                edgecolor="black",
                alpha=alpha,
                label=f"Zone {zone.id()}",
            )
            ax.add_patch(polygon)

            if show_centroids:
                centroid = zone.centroid()
                ax.scatter(
                    [centroid.lat()],
                    [centroid.lon()],
                    color="red",
                    s=30,
                    zorder=5,
                    marker="x",
                )

            if show_corner_labels:
                ax.text(
                    min(xs) + 0.0001,
                    min(ys) + 0.0001,
                    zone.id(),
                    fontsize=10,
                    ha="left",
                    va="bottom",
                    weight="bold",
                    alpha=0.7,
                    zorder=3,
                )

    def _draw_routes(
        self,
        ax,
        transit_network: TransitNetwork,
        *,
        linewidth: float,
        alpha: float,
        show_markers: bool,
        show_mid_labels: bool,
    ) -> None:
        for index, route in enumerate(transit_network.routes()):
            shape = self._resolve_route_shape(route, transit_network)
            if len(shape) < 2:
                continue

            xs = [point.lat() for point in shape]
            ys = [point.lon() for point in shape]
            color = self.ROUTE_COLORS[index % len(self.ROUTE_COLORS)]

            plot_kwargs = {
                "color": color,
                "linewidth": linewidth,
                "alpha": alpha,
                "label": route.id(),
                "zorder": 4,
            }
            if show_markers:
                plot_kwargs.update(
                    {
                        "marker": "o",
                        "markersize": 12,
                        "markerfacecolor": "white",
                        "markeredgewidth": 2,
                        "markeredgecolor": color,
                    }
                )

            ax.plot(xs, ys, **plot_kwargs)

            if show_mid_labels:
                mid_index = len(xs) // 2
                ax.text(
                    xs[mid_index],
                    ys[mid_index],
                    f" {route.id()} ",
                    color="white",
                    bbox=dict(
                        facecolor=color,
                        edgecolor="none",
                        boxstyle="round,pad=0.2",
                        alpha=0.8,
                    ),
                    fontsize=9,
                    weight="bold",
                    zorder=6,
                )

    def _resolve_route_shape(
        self,
        route: Route,
        transit_network: TransitNetwork,
    ):
        shape = route.shape()
        if shape:
            return shape
        return [
            transit_network.get_stop_by_id(stop_id).coord()
            for stop_id in route.stops_seq()
            if transit_network.get_stop_by_id(stop_id)
        ]

    def _draw_stops(
        self,
        ax,
        transit_network: TransitNetwork,
        *,
        scatter_size: float,
        label_fontsize: float,
        x_offset: float = 0.0,
        y_offset: float = 0.0,
        show_labels: bool = False,
        label_stop_ids: set[str] | None = None,
    ) -> None:
        stops_x = [stop.coord().lat() for stop in transit_network.stops()]
        stops_y = [stop.coord().lon() for stop in transit_network.stops()]
        ax.scatter(
            stops_x,
            stops_y,
            color="black",
            zorder=5,
            s=scatter_size,
            label="Stops",
        )

        label_stop_ids = label_stop_ids or set()
        for stop in transit_network.stops():
            should_label = show_labels or stop.id() in label_stop_ids
            if not should_label:
                continue

            ax.text(
                stop.coord().lat() + x_offset,
                stop.coord().lon() + y_offset,
                stop.id(),
                fontsize=label_fontsize,
                ha="center" if x_offset == 0.0 else "left",
                va="top" if y_offset < 0 else "center",
                color="black",
                zorder=10,
            )

    def _draw_highlighted_stops(
        self,
        ax,
        transit_network: TransitNetwork,
        highlight_stop_ids: list[str],
        buffer_radius_m: float | None,
    ) -> None:
        highlight_ids = set(highlight_stop_ids)
        highlighted_stops = [
            stop for stop in transit_network.stops() if stop.id() in highlight_ids
        ]
        if not highlighted_stops:
            return

        ax.scatter(
            [stop.coord().lat() for stop in highlighted_stops],
            [stop.coord().lon() for stop in highlighted_stops],
            color="orange",
            edgecolors="darkred",
            linewidths=1.5,
            zorder=7,
            s=100,
            label="Highlighted Stops",
        )

        if not buffer_radius_m or buffer_radius_m <= 0:
            return

        for index, stop in enumerate(highlighted_stops):
            lat = stop.coord().lat()
            lon = stop.coord().lon()
            lat_radius_deg = buffer_radius_m / 111320.0
            lon_scale = max(math.cos(math.radians(lat)), 1e-6)
            lon_radius_deg = buffer_radius_m / (111320.0 * lon_scale)
            ellipse = patches.Ellipse(
                (lat, lon),
                width=lat_radius_deg * 2,
                height=lon_radius_deg * 2,
                facecolor="orange",
                edgecolor="darkred",
                alpha=0.15,
                linewidth=1.5,
                zorder=6,
                label="Coverage Buffer" if index == 0 else None,
            )
            ax.add_patch(ellipse)

    def _draw_od_pairs(self, ax, od_matrix: ODMatrix) -> None:
        max_demand = (
            max((od_pair.demand() for od_pair in od_matrix.od_pairs()), default=1.0) or 1.0
        )
        drawn_pairs = set()

        for od_pair in od_matrix.od_pairs():
            if od_pair.demand() <= 0:
                continue

            origin_zone = od_matrix.get_zone_by_id(od_pair.origin_zone_id())
            destination_zone = od_matrix.get_zone_by_id(od_pair.destination_zone_id())
            if not origin_zone or not destination_zone:
                continue

            origin_centroid = origin_zone.centroid()
            destination_centroid = destination_zone.centroid()
            line_width = max(1.0, (od_pair.demand() / max_demand) * 8.0)

            pair_key = tuple(
                sorted([od_pair.origin_zone_id(), od_pair.destination_zone_id()])
            )
            rad = -0.2 if pair_key in drawn_pairs else 0.2
            drawn_pairs.add(pair_key)

            ax.annotate(
                "",
                xy=(destination_centroid.lat(), destination_centroid.lon()),
                xycoords="data",
                xytext=(origin_centroid.lat(), origin_centroid.lon()),
                textcoords="data",
                arrowprops=dict(
                    arrowstyle="->,head_width=0.6,head_length=0.8",
                    color="#d62728",
                    lw=line_width,
                    alpha=0.7,
                    connectionstyle=f"arc3,rad={rad}",
                ),
                zorder=7,
            )

            mid_x = (origin_centroid.lat() + destination_centroid.lat()) / 2
            mid_y = (origin_centroid.lon() + destination_centroid.lon()) / 2
            dx = destination_centroid.lat() - origin_centroid.lat()
            dy = destination_centroid.lon() - origin_centroid.lon()
            length = math.sqrt(dx**2 + dy**2)
            if length > 0:
                offset = 100 / 100000.0
                nx = -dy / length
                ny = dx / length
                mid_x -= nx * offset * rad * 2
                mid_y -= ny * offset * rad * 2

            ax.text(
                mid_x,
                mid_y,
                self._format_demand_label(od_pair.demand()),
                color="black",
                fontsize=9,
                weight="bold",
                ha="center",
                va="center",
                bbox=dict(
                    facecolor="white",
                    edgecolor="none",
                    boxstyle="circle,pad=0.2",
                    alpha=0.8,
                ),
                zorder=8,
            )

    def _format_demand_label(self, demand: float) -> str:
        if float(demand).is_integer():
            return str(int(demand))
        return f"{demand:.2f}"

    def _build_od_footer_text(
        self,
        od_matrix: ODMatrix,
        total_od_count: int | None = None,
    ) -> str:
        od_pairs = od_matrix.od_pairs()
        visible_count = len(od_pairs)
        summary = f"OD Pairs: showing {visible_count}"
        if total_od_count is not None and total_od_count != visible_count:
            summary += f" of {total_od_count}"

        preview_limit = 8
        od_lines = [summary]
        preview_pairs = od_pairs[:preview_limit]
        for index in range(0, len(preview_pairs), 2):
            chunk = preview_pairs[index : index + 2]
            od_lines.append(
                " | ".join(
                    [
                        f"{od_pair.id()}: {od_pair.origin_zone_id()} -> {od_pair.destination_zone_id()}"
                        for od_pair in chunk
                    ]
                )
            )
        if visible_count > preview_limit:
            od_lines.append("...")
        return "\n".join(od_lines)

    def _build_route_footer_text(self, transit_network: TransitNetwork) -> str:
        routes = transit_network.routes()
        preview_limit = 8
        route_lines = [f"Routes: {len(routes)} | Stops: {len(transit_network.stops())}"]
        for route in routes[:preview_limit]:
            route_lines.append(f"{route.id()}: {' -> '.join(route.stops_seq())}")
        if len(routes) > preview_limit:
            route_lines.append("...")
        return "\n".join(route_lines)

    def _apply_common_layout(
        self,
        fig,
        ax,
        title: str,
        *,
        footer_text: str | None = None,
        footer_box_color: str = "wheat",
        footer_rect=None,
        legend_title: str | None = None,
    ) -> None:
        ax.set_aspect("equal", adjustable="datalim")
        ax.set_title(title, fontsize=16, pad=20)
        ax.grid(True, linestyle="--", alpha=0.4)

        handles, labels = ax.get_legend_handles_labels()
        legend_entries = dict(zip(labels, handles))
        if legend_entries:
            ax.legend(
                legend_entries.values(),
                legend_entries.keys(),
                title=legend_title,
                bbox_to_anchor=(1.02, 1),
                loc="upper left",
                fontsize=9,
            )

        if footer_text:
            fig.text(
                0.5,
                0.02,
                footer_text,
                wrap=True,
                horizontalalignment="center",
                fontsize=9,
                bbox=dict(
                    facecolor=footer_box_color,
                    alpha=0.35,
                    boxstyle="round,pad=0.5",
                ),
            )

        fig.tight_layout(rect=footer_rect)

    def _save_or_show(self, fig, save_path) -> None:
        if save_path:
            save_path_obj = Path(save_path)
            save_path_obj.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(save_path_obj, dpi=self.SAVE_DPI)
            print(f"Saved plot to {save_path_obj}")
        else:
            plt.show()
        plt.close(fig)
