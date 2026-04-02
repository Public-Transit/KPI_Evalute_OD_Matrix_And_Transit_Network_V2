import math

import matplotlib
import matplotlib.patches as patches

from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork


matplotlib.use("Agg")
import matplotlib.pyplot as plt


class VisualizeZoneAndTransitNetwork:
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

    def show(
        self,
        od_matrix: ODMatrix,
        transit_network: TransitNetwork,
        save_path=None,
        title=None,
        highlight_stop_ids=None,
        buffer_radius_m=None,
    ):
        fig, ax = plt.subplots(figsize=(10, 10))

        self._draw_zones(
            ax,
            od_matrix,
            alpha=0.5,
            show_centroids=False,
            show_corner_labels=False,
        )
        self._draw_routes(
            ax,
            transit_network,
            linewidth=5,
            alpha=0.8,
            show_markers=True,
            show_mid_labels=False,
        )
        self._draw_stops(
            ax,
            transit_network,
            scatter_size=20,
            label_fontsize=8,
            x_offset=0.00005,
            y_offset=-0.0001,
        )
        self._draw_highlighted_stops(
            ax,
            transit_network,
            highlight_stop_ids or [],
            buffer_radius_m,
        )
        self._apply_common_layout(
            fig,
            ax,
            title or "Transit Network Visualization",
            footer_text=self._build_od_footer_text(od_matrix),
            footer_rect=[0, 0.12, 1, 1],
        )
        self._save_or_show(fig, save_path)

    def show_zones_and_routes(
        self,
        od_matrix: ODMatrix,
        transit_network: TransitNetwork,
        save_path=None,
        title=None,
    ):
        fig, ax = plt.subplots(figsize=(12, 12))

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
            alpha=0.6,
            show_markers=False,
            show_mid_labels=True,
        )
        self._draw_stops(
            ax,
            transit_network,
            scatter_size=15,
            label_fontsize=7,
            y_offset=-0.00015,
        )
        self._apply_common_layout(
            fig,
            ax,
            title or "Placeholder Network Routes and Stops",
            footer_text=self._build_route_footer_text(transit_network),
            footer_box_color="lightgrey",
            footer_rect=[0, 0.15, 1, 1],
            legend_title="Legend",
        )
        self._save_or_show(fig, save_path)

    def show_zones_and_od(self, od_matrix: ODMatrix, save_path=None, title=None):
        fig, ax = plt.subplots(figsize=(12, 12))

        self._draw_zones(
            ax,
            od_matrix,
            alpha=0.3,
            show_centroids=True,
            show_corner_labels=True,
        )
        self._draw_od_pairs(ax, od_matrix)
        self._apply_common_layout(
            fig,
            ax,
            title or "Placeholder OD Demand Map",
            legend_title="Zones",
        )
        self._save_or_show(fig, save_path)

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
                    s=40,
                    zorder=5,
                    marker="x",
                )

            if show_corner_labels:
                ax.text(
                    min(xs) + 0.0001,
                    min(ys) + 0.0001,
                    zone.id(),
                    fontsize=20,
                    ha="left",
                    va="bottom",
                    weight="bold",
                    alpha=0.4,
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
            shape = route.shape()
            if not shape:
                shape = [
                    transit_network.get_stop_by_id(stop_id).coord()
                    for stop_id in route.stops_seq()
                    if transit_network.get_stop_by_id(stop_id)
                ]

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

            if show_mid_labels and len(xs) > 1:
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

    def _draw_stops(
        self,
        ax,
        transit_network: TransitNetwork,
        *,
        scatter_size: float,
        label_fontsize: float,
        x_offset: float = 0.0,
        y_offset: float = 0.0,
    ) -> None:
        stops_x = [stop.coord().lat() for stop in transit_network.stops()]
        stops_y = [stop.coord().lon() for stop in transit_network.stops()]
        ax.scatter(stops_x, stops_y, color="black", zorder=5, s=scatter_size, label="Stops")

        for stop in transit_network.stops():
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
        max_demand = max((od_pair.demand() for od_pair in od_matrix.od_pairs()), default=1.0) or 1.0
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

            pair_key = tuple(sorted([od_pair.origin_zone_id(), od_pair.destination_zone_id()]))
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
                str(int(od_pair.demand())),
                color="black",
                fontsize=10,
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

    def _build_od_footer_text(self, od_matrix: ODMatrix) -> str:
        od_lines = []
        od_pairs = od_matrix.od_pairs()
        for index in range(0, len(od_pairs), 4):
            chunk = od_pairs[index : index + 4]
            od_lines.append(
                " | ".join(
                    [
                        f"{od_pair.id()}: {od_pair.origin_zone_id()} -> {od_pair.destination_zone_id()}"
                        for od_pair in chunk
                    ]
                )
            )
        return "OD Pairs:\n" + "\n".join(od_lines)

    def _build_route_footer_text(self, transit_network: TransitNetwork) -> str:
        route_lines = [
            f"{route.id()}: {' -> '.join(route.stops_seq())}"
            for route in transit_network.routes()
        ]
        return "Stop Sequences:\n" + "\n".join(route_lines)

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
                bbox=dict(facecolor=footer_box_color, alpha=0.35, boxstyle="round,pad=0.5"),
            )

        fig.tight_layout(rect=footer_rect)

    def _save_or_show(self, fig, save_path) -> None:
        if save_path:
            fig.savefig(save_path, dpi=200)
            print(f"Saved plot to {save_path}")
        else:
            plt.show()
        plt.close(fig)
