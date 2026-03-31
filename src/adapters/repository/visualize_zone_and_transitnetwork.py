import matplotlib.pyplot as plt
import matplotlib.patches as patches

from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork

class VisualizeZoneAndTransitNetwork:
    def __init__(self):
        pass
    
    def show(self, od_matrix: ODMatrix, transit_network: TransitNetwork, save_path=None, title=None):
        # ==========================================
        # CẤU HÌNH HIỂN THỊ (Sửa True/False để bật/tắt)
        # ==========================================
        SHOW_ZONE_LABELS = False
        SHOW_ROUTE_LABELS = False
        SHOW_STOP_LABELS = True
        SHOW_OD_ARROWS = True
        # ==========================================

        fig, ax = plt.subplots(figsize=(10, 10))
        
        # 1. Vẽ các Zone
        colors = ['#ff9999', '#99ff99', '#9999ff', '#ffff99']
        for i, zone in enumerate(od_matrix.zones()):
            boundary = zone.boundary()
            xs = [p.lat() for p in boundary]  # Hệ toạ độ xy với lat=x, lon=y
            ys = [p.lon() for p in boundary]
            
            polygon = patches.Polygon(xy=list(zip(xs, ys)), closed=True, 
                                      facecolor=colors[i % len(colors)], 
                                      edgecolor='black', alpha=0.5, label=f'Zone {zone.id()}')
            ax.add_patch(polygon)
            
            if SHOW_ZONE_LABELS:
                centroid = zone.centroid()
                ax.text(centroid.lat(), centroid.lon(), f'Zone {zone.id()}', 
                        fontsize=14, ha='center', va='center', weight='bold', zorder=3)

        # 2. Vẽ Transit Network (Routes)
        route_colors = ['red', 'blue', 'green', 'magenta', 'purple']
        for i, route in enumerate(transit_network.routes()):
            shape = route.shape()
            xs = [p.lat() for p in shape]
            ys = [p.lon() for p in shape]
            
            # Vẽ line và các điểm marker tròn cho từng "trạm" mà tuyến đi qua
            ax.plot(xs, ys, color=route_colors[i % len(route_colors)], linewidth=5, 
                    alpha=0.8, marker='o', markersize=12, markerfacecolor='white', 
                    markeredgewidth=2, markeredgecolor=route_colors[i % len(route_colors)],
                    label=route.id(), zorder=4)
            
            # Điền tên Route ở giữa đoạn đường để dễ nhìn (scale Lat/Lon offset to ~0.00008)
            if SHOW_ROUTE_LABELS and len(xs) > 1:
                mid_idx = len(xs) // 2
                ax.text(xs[mid_idx], ys[mid_idx] + 0.00008, f" {route.id()} ", color='white', 
                        bbox=dict(facecolor=route_colors[i % len(route_colors)], edgecolor='none', boxstyle='round,pad=0.2'),
                        fontsize=10, weight='bold', zorder=6)

        # 3. Vẽ danh sách Stops chung của hệ thống
        stops_x = [stop.coord().lat() for stop in transit_network.stops()]
        stops_y = [stop.coord().lon() for stop in transit_network.stops()]
        # Làm nổi bật điểm dừng chung bằng chấm đen nhỏ ở chính giữa tâm
        ax.scatter(stops_x, stops_y, color='black', zorder=5, s=20, label='Mạng lưới Stops')
        
        # Thêm mã Stop cạnh trạm (scale Lat/Lon offset ~ 0.00005)
        if SHOW_STOP_LABELS:
            for stop in transit_network.stops():
                # Set zorder=10 để Stop Text luôn nằm trên cùng, không bị đè
                ax.text(stop.coord().lat() + 0.00005, stop.coord().lon() - 0.0001, stop.id(), 
                        fontsize=8, color='black', weight='bold', zorder=10)

        # 4. Vẽ mũi tên các cặp OD nếu được bật
        if SHOW_OD_ARROWS:
            for od in od_matrix.od_pairs():
                o_zone_lst = [z for z in od_matrix.zones() if z.id() == od.origin_zone_id()]
                d_zone_lst = [z for z in od_matrix.zones() if z.id() == od.destination_zone_id()]
                if not o_zone_lst or not d_zone_lst: continue
                
                o_c = o_zone_lst[0].centroid()
                d_c = d_zone_lst[0].centroid()
                
                ax.annotate(
                    f"{od.id()} (Demand:{od.demand()})",
                    xy=(d_c.lat(), d_c.lon()), xycoords='data',
                    xytext=(o_c.lat(), o_c.lon()), textcoords='data',
                    arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6",
                                    color="orange",
                                    lw=2,
                                    connectionstyle="arc3,rad=0.15"), 
                    color="brown",
                    fontsize=9,
                    fontweight="bold",
                    ha="center",
                    va="center",
                    zorder=7,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="orange", alpha=0.9)
                )

        # Tự động scale
        ax.set_aspect('equal', adjustable='datalim')
        
        if title:
            ax.set_title(title, fontsize=16)
        else:
            ax.set_title("Chế mô phỏng: Transit Network 3x3 Grid", fontsize=16)
        
        # Sắp xếp legend không bị trùng lặp
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.grid(True, linestyle='--', alpha=0.6)
        
        # Thêm thông tin OD Pairs ở đáy
        od_pairs = od_matrix.od_pairs()
        od_lines = []
        for i in range(0, len(od_pairs), 4):
            chunk = od_pairs[i:i+4]
            od_lines.append(" | ".join([f"{od.id()}: {od.origin_zone_id()} -> {od.destination_zone_id()}" for od in chunk]))
        
        od_text = "Danh sach OD Pairs:\n" + "\n".join(od_lines)
        plt.figtext(0.5, 0.02, od_text, wrap=True, horizontalalignment='center', fontsize=10, 
                    bbox=dict(facecolor='wheat', alpha=0.5, boxstyle='round,pad=0.5'))
                    
        # Dành chỗ trống bằng rect để figtext không bị đè
        plt.tight_layout(rect=[0, 0.12, 1, 1])
        
        if save_path:
            plt.savefig(save_path, dpi=200)
            print(f"Lưu plot thành công tại {save_path}")
        else:
            plt.show()
