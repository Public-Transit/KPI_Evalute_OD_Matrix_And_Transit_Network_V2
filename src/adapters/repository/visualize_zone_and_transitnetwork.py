import math

import matplotlib
import matplotlib.patches as patches

from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork


matplotlib.use("Agg")
import matplotlib.pyplot as plt


class VisualizeZoneAndTransitNetwork:
    def __init__(self):
        pass

    def show(
        self,
        od_matrix: ODMatrix,
        transit_network: TransitNetwork,
        save_path=None,
        title=None,
        highlight_stop_ids=None,
        buffer_radius_m=None,
    ):
        show_zone_labels = False
        show_route_labels = False
        show_stop_labels = True

        fig, ax = plt.subplots(figsize=(10, 10))

        colors = ["#ff9999", "#99ff99", "#9999ff", "#ffff99"]
        for i, zone in enumerate(od_matrix.zones()):
            boundary = zone.boundary()
            xs = [p.lat() for p in boundary]
            ys = [p.lon() for p in boundary]

            polygon = patches.Polygon(
                xy=list(zip(xs, ys)),
                closed=True,
                facecolor=colors[i % len(colors)],
                edgecolor="black",
                alpha=0.5,
                label=f"Zone {zone.id()}",
            )
            ax.add_patch(polygon)

            if show_zone_labels:
                centroid = zone.centroid()
                ax.text(
                    centroid.lat(),
                    centroid.lon(),
                    f"Zone {zone.id()}",
                    fontsize=14,
                    ha="center",
                    va="center",
                    weight="bold",
                    zorder=3,
                )

        route_colors = ["red", "blue", "green", "magenta", "purple"]
        for i, route in enumerate(transit_network.routes()):
            shape = route.shape()
            xs = [p.lat() for p in shape]
            ys = [p.lon() for p in shape]

            ax.plot(
                xs,
                ys,
                color=route_colors[i % len(route_colors)],
                linewidth=5,
                alpha=0.8,
                marker="o",
                markersize=12,
                markerfacecolor="white",
                markeredgewidth=2,
                markeredgecolor=route_colors[i % len(route_colors)],
                label=route.id(),
                zorder=4,
            )

            if show_route_labels and len(xs) > 1:
                mid_idx = len(xs) // 2
                ax.text(
                    xs[mid_idx],
                    ys[mid_idx] + 0.00008,
                    f" {route.id()} ",
                    color="white",
                    bbox=dict(
                        facecolor=route_colors[i % len(route_colors)],
                        edgecolor="none",
                        boxstyle="round,pad=0.2",
                    ),
                    fontsize=10,
                    weight="bold",
                    zorder=6,
                )

        stops_x = [stop.coord().lat() for stop in transit_network.stops()]
        stops_y = [stop.coord().lon() for stop in transit_network.stops()]
        ax.scatter(stops_x, stops_y, color="black", zorder=5, s=20, label="Network Stops")

        highlight_stop_ids = highlight_stop_ids or []
        highlight_stop_set = set(highlight_stop_ids)
        highlighted_stops = [stop for stop in transit_network.stops() if stop.id() in highlight_stop_set]

        if highlighted_stops:
            highlight_x = [stop.coord().lat() for stop in highlighted_stops]
            highlight_y = [stop.coord().lon() for stop in highlighted_stops]
            ax.scatter(
                highlight_x,
                highlight_y,
                color="orange",
                edgecolors="darkred",
                linewidths=1.5,
                zorder=7,
                s=100,
                label="Spatial Coverage Stops",
            )

            if buffer_radius_m and buffer_radius_m > 0:
                for stop in highlighted_stops:
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
                        label="Coverage Buffer",
                    )
                    ax.add_patch(ellipse)

        if show_stop_labels:
            for stop in transit_network.stops():
                ax.text(
                    stop.coord().lat() + 0.00005,
                    stop.coord().lon() - 0.0001,
                    stop.id(),
                    fontsize=8,
                    color="black",
                    weight="bold",
                    zorder=10,
                )

        ax.set_aspect("equal", adjustable="datalim")
        ax.set_title(title or "Transit Network Visualization", fontsize=16)

        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.05, 1), loc="upper left")

        plt.grid(True, linestyle="--", alpha=0.6)

        od_pairs = od_matrix.od_pairs()
        od_lines = []
        for i in range(0, len(od_pairs), 4):
            chunk = od_pairs[i : i + 4]
            od_lines.append(" | ".join([f"{od.id()}: {od.origin_zone_id()} -> {od.destination_zone_id()}" for od in chunk]))

        od_text = "Danh sach OD Pairs:\n" + "\n".join(od_lines)
        plt.figtext(
            0.5,
            0.02,
            od_text,
            wrap=True,
            horizontalalignment="center",
            fontsize=10,
            bbox=dict(facecolor="wheat", alpha=0.5, boxstyle="round,pad=0.5"),
        )

        plt.tight_layout(rect=[0, 0.12, 1, 1])

        if save_path:
            plt.savefig(save_path, dpi=200)
            print(f"Luu plot thanh cong tai {save_path}")
        else:
            plt.show()
