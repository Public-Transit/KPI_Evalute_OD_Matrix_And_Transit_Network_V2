import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
import numpy as np

from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork

class VisualizeZoneAndTransitNetwork:
    def __init__(self):
        pass
    
    def show_zones_and_routes(self, od_matrix: ODMatrix, transit_network: TransitNetwork, save_path=None, title=None):
        """
        Plot 1: Hiển thị Zones, Routes, Stops (không có OD).
        Cấu hình style như yêu cầu:
        - Tên zone Z1, Z2... góc trái dưới, mờ nhưng to.
        - Tâm zone màu đỏ.
        - Stop s1, s2... nhỏ, dưới điểm stop.
        """
        fig, ax = plt.subplots(figsize=(12, 12))
        
        # 1. Vẽ các Zone
        colors = ['#ff9999', '#99ff99', '#9999ff', '#ffff99', '#ffcc99', '#cc99ff', '#99ffff', '#ffb3e6', '#c2c2f0']
        for i, zone in enumerate(od_matrix.zones()):
            boundary = zone.boundary()
            xs = [p.lat() for p in boundary]
            ys = [p.lon() for p in boundary]
            
            polygon = patches.Polygon(xy=list(zip(xs, ys)), closed=True, 
                                      facecolor=colors[i % len(colors)], 
                                      edgecolor='black', alpha=0.3, label=f'Zone {zone.id()}')
            ax.add_patch(polygon)
            
            # Tâm zone màu đỏ
            centroid = zone.centroid()
            ax.scatter([centroid.lat()], [centroid.lon()], color='red', s=40, zorder=5, marker='x')
            
            # Tên zone góc trái dưới (Tìm điểm min X, min Y)
            min_x, min_y = min(xs), min(ys)
            ax.text(min_x + 0.0001, min_y + 0.0001, f'{zone.id()}', 
                    fontsize=20, ha='left', va='bottom', weight='bold', alpha=0.4, zorder=3)

        # 2. Vẽ Transit Network (Routes)
        route_colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0']
        for i, route in enumerate(transit_network.routes()):
            shape = route.shape()
            if not shape:  # Fallback to stops if shape is empty
                shape = [transit_network.get_stop_by_id(sid).coord() for sid in route.stops_seq() if transit_network.get_stop_by_id(sid)]
                
            xs = [p.lat() for p in shape]
            ys = [p.lon() for p in shape]
            
            ax.plot(xs, ys, color=route_colors[i % len(route_colors)], linewidth=4, 
                    alpha=0.6, label=route.id(), zorder=4)
            
            if len(xs) > 1:
                mid_idx = len(xs) // 2
                ax.text(xs[mid_idx], ys[mid_idx], f" {route.id()} ", color='white', 
                        bbox=dict(facecolor=route_colors[i % len(route_colors)], edgecolor='none', boxstyle='round,pad=0.2', alpha=0.8),
                        fontsize=9, weight='bold', zorder=6)

        # 3. Vẽ danh sách Stops chung
        stops_x = [stop.coord().lat() for stop in transit_network.stops()]
        stops_y = [stop.coord().lon() for stop in transit_network.stops()]
        ax.scatter(stops_x, stops_y, color='black', zorder=5, s=15, label='Stops')
        
        # Thêm tên Stop nhỏ, bên dưới điểm
        for stop in transit_network.stops():
            ax.text(stop.coord().lat(), stop.coord().lon() - 0.00015, stop.id(), 
                    fontsize=7, ha='center', va='top', color='black', zorder=10)

        # Thêm Legend cho Routes và Zones
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), 
                  title="Ghi chú", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)

        # 4. Thêm thông tin Stop Sequences ở phía dưới hình
        route_info_lines = []
        for route in transit_network.routes():
            seq_str = " -> ".join(route.stops_seq())
            route_info_lines.append(f"{route.id()}: {seq_str}")
        
        info_text = "Danh sách Trạm dừng (Stop Sequences):\n" + "\n".join(route_info_lines)
        plt.figtext(0.5, 0.02, info_text, wrap=True, horizontalalignment='center', fontsize=9, 
                    bbox=dict(facecolor='lightgrey', alpha=0.3, boxstyle='round,pad=0.5'))

        ax.set_aspect('equal', adjustable='datalim')
        if title:
            ax.set_title(title, fontsize=16, pad=20)
        else:
            ax.set_title("Bản đồ Tuyến xe & Điểm dừng (Routes & Stops)", fontsize=16, pad=20)
        
        plt.grid(True, linestyle='--', alpha=0.4)
        
        # Chừa khoảng trống phía dưới cho text (rect=[left, bottom, right, top])
        plt.tight_layout(rect=[0, 0.15, 1, 1])
        
        if save_path:
            plt.savefig(save_path, dpi=200)
            print(f"Lưu plot route thành công tại {save_path}")
        else:
            plt.show()

    def show_zones_and_od(self, od_matrix: ODMatrix, save_path=None, title=None):
        """
        Plot 2: Chỉ hiển thị Zones và các cặp OD (Mũi tên cong, độ dày theo demand, có số liệu).
        """
        fig, ax = plt.subplots(figsize=(12, 12))
        
        # 1. Vẽ các Zone
        colors = ['#ff9999', '#99ff99', '#9999ff', '#ffff99', '#ffcc99', '#cc99ff', '#99ffff', '#ffb3e6', '#c2c2f0']
        for i, zone in enumerate(od_matrix.zones()):
            boundary = zone.boundary()
            xs = [p.lat() for p in boundary]
            ys = [p.lon() for p in boundary]
            
            polygon = patches.Polygon(xy=list(zip(xs, ys)), closed=True, 
                                      facecolor=colors[i % len(colors)], 
                                      edgecolor='black', alpha=0.3, label=f'Zone {zone.id()}')
            ax.add_patch(polygon)
            
            # Tâm zone màu đỏ
            centroid = zone.centroid()
            ax.scatter([centroid.lat()], [centroid.lon()], color='red', s=40, zorder=5, marker='x')
            
            min_x, min_y = min(xs), min(ys)
            ax.text(min_x + 0.0001, min_y + 0.0001, f'{zone.id()}', 
                    fontsize=20, ha='left', va='bottom', weight='bold', alpha=0.4, zorder=3)

        # 4. Vẽ mũi tên các cặp OD
        max_demand = 1.0
        if od_matrix.od_pairs():
            max_demand = max([od.demand() for od in od_matrix.od_pairs()])
            if max_demand == 0: max_demand = 1.0

        drawn_pairs = set()

        for od in od_matrix.od_pairs():
            if od.demand() <= 0: continue
            
            o_zone_lst = [z for z in od_matrix.zones() if z.id() == od.origin_zone_id()]
            d_zone_lst = [z for z in od_matrix.zones() if z.id() == od.destination_zone_id()]
            if not o_zone_lst or not d_zone_lst: continue
            
            o_c = o_zone_lst[0].centroid()
            d_c = d_zone_lst[0].centroid()
            
            # Tính line width dựa vào max demand (min=1, max=8)
            lw = max(1, (od.demand() / max_demand) * 8)
            
            # Rad để mũi tên hơi cong, tránh bị đè nếu có đường ngược lại
            rad = 0.2
            pair_key = tuple(sorted([od.origin_zone_id(), od.destination_zone_id()]))
            if pair_key in drawn_pairs:
                rad = -0.2 # cong ngược lại để không đè
            drawn_pairs.add(pair_key)
            
            ax.annotate(
                "",
                xy=(d_c.lat(), d_c.lon()), xycoords='data',
                xytext=(o_c.lat(), o_c.lon()), textcoords='data',
                arrowprops=dict(arrowstyle="->,head_width=0.6,head_length=0.8",
                                color="#d62728",
                                lw=lw,
                                alpha=0.7,
                                connectionstyle=f"arc3,rad={rad}"), 
                zorder=7
            )
            
            # Tính điểm giữa đường cong để hiện số lượng OD
            mid_x = (o_c.lat() + d_c.lat()) / 2
            mid_y = (o_c.lon() + d_c.lon()) / 2
            
            # Hiệu chỉnh nhẹ theo rad
            # Hiệu chỉnh offset về đúng tỉ lệ Lat/Lon (100,000m ~ 1 degree)
            offset = 100 / 100000.0 

            dx = d_c.lat() - o_c.lat()
            dy = d_c.lon() - o_c.lon()
            length = math.sqrt(dx**2 + dy**2)
            if length > 0:
                nx = -dy / length
                ny = dx / length
                mid_x -= nx * offset * rad * 2
                mid_y -= ny * offset * rad * 2

            ax.text(mid_x, mid_y, str(int(od.demand())), color='black', 
                    fontsize=10, weight='bold', ha='center', va='center',
                    bbox=dict(facecolor='white', edgecolor='none', boxstyle='circle,pad=0.2', alpha=0.8), zorder=8)

        # Thêm Legend cho Zones
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), 
                  title="Phân vùng (Zones)", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)

        ax.set_aspect('equal', adjustable='datalim')
        if title:
            ax.set_title(title, fontsize=16, pad=20)
        else:
            ax.set_title("Bản đồ Nhu cầu OD (Lưu lượng di chuyển)", fontsize=16, pad=20)
        
        plt.grid(True, linestyle='--', alpha=0.4)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=200)
            print(f"Lưu plot OD thành công tại {save_path}")
        else:
            plt.show()
