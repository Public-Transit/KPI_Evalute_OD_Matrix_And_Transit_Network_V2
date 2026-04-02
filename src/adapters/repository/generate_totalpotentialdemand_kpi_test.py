import os
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from src.adapters.repository.fake_repo_totalpotentialdemand_case1 import FakeRepoTotalPotentialDemandCase1
from src.adapters.repository.fake_repo_totalpotentialdemand_case2 import FakeRepoTotalPotentialDemandCase2
from src.adapters.repository.fake_repo_totalpotentialdemand_case3 import FakeRepoTotalPotentialDemandCase3
from src.adapters.repository.fake_repo_totalpotentialdemand_case4 import FakeRepoTotalPotentialDemandCase4
from src.adapters.repository.fake_repo_totalpotentialdemand_case5 import FakeRepoTotalPotentialDemandCase5

def draw_case(case_id, save_path):
    repo_map = {
        1: FakeRepoTotalPotentialDemandCase1,
        2: FakeRepoTotalPotentialDemandCase2,
        3: FakeRepoTotalPotentialDemandCase3,
        4: FakeRepoTotalPotentialDemandCase4,
        5: FakeRepoTotalPotentialDemandCase5,
    }
    repo_class = repo_map.get(case_id)
    if not repo_class:
        return
    
    repo = repo_class()
    stops, routes, zones, od_pairs, trips = repo.get()
    
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.subplots_adjust(bottom=0.25)
    
    colors = ['#ff9999', '#99ff99', '#9999ff', '#ffff99', '#ffcc99', '#cc99ff', '#99ffff', '#ffb3e6']
    for i, zone in enumerate(zones):
        boundary = zone.boundary()
        xs = [p.lat() for p in boundary]
        ys = [p.lon() for p in boundary]
        
        polygon = patches.Polygon(xy=list(zip(xs, ys)), closed=True, 
                                  facecolor=colors[i % len(colors)], 
                                  edgecolor='black', alpha=0.3)
        ax.add_patch(polygon)
        
        centroid = zone.centroid()
        ax.scatter([centroid.lat()], [centroid.lon()], color='red', s=40, zorder=5, marker='x')
        min_x, min_y = min(xs), min(ys)
        ax.text(min_x + 0.0001, min_y + 0.0001, f'{zone.id()}', 
                fontsize=16, ha='left', va='bottom', weight='bold', alpha=0.5, zorder=3)

    for od in od_pairs:
        o_zone = next((z for z in zones if z.id() == od.origin_zone_id()), None)
        d_zone = next((z for z in zones if z.id() == od.destination_zone_id()), None)
        if not o_zone or not d_zone: continue
        
        o_c = o_zone.centroid()
        d_c = d_zone.centroid()
        
        ax.annotate(
            "",
            xy=(d_c.lat(), d_c.lon()), xycoords='data',
            xytext=(o_c.lat(), o_c.lon()), textcoords='data',
            arrowprops=dict(arrowstyle="->,head_width=0.8,head_length=1.0",
                            color="#d62728", lw=4, alpha=0.6, connectionstyle=f"arc3,rad=0.2"), 
            zorder=6
        )
        mid_x = (o_c.lat() + d_c.lat()) / 2
        mid_y = (o_c.lon() + d_c.lon()) / 2
        dx = d_c.lat() - o_c.lat()
        dy = d_c.lon() - o_c.lon()
        length = math.sqrt(dx**2 + dy**2)
        if length > 0:
            nx = -dy / length
            ny = dx / length
            mid_x -= nx * 0.0005
            mid_y -= ny * 0.0005

        ax.text(mid_x, mid_y, "Demand: " + str(int(od.demand())), color='black', 
                fontsize=12, weight='bold', ha='center', va='center',
                bbox=dict(facecolor='white', edgecolor='red', boxstyle='round,pad=0.3', alpha=0.9), zorder=8)

    route_colors = ['#1f77b4', '#9467bd', '#e377c2']
    route_info_texts = []
    for i, route in enumerate(routes):
        shape = route.shape()
        xs = [p.lat() for p in shape]
        ys = [p.lon() for p in shape]
        
        ax.plot(xs, ys, color=route_colors[i % len(route_colors)], linewidth=2, 
                alpha=0.7, label=f'Route {route.id()}', zorder=4, linestyle='--')
                
        route_info_texts.append(f"Route {route.id()}: {' -> '.join(route.stops_seq())}")

    candidate_stops = repo.candidate_trips_for_vis[0]
    
    # Phân tích Candidate Trip thành các Routes
    c_route_legs = []
    current_route = None
    current_leg_stops = []
    
    for i in range(len(candidate_stops) - 1):
        s1, s2 = candidate_stops[i], candidate_stops[i+1]
        valid_routes = []
        for r in routes:
            seq = r.stops_seq()
            if s1 in seq and s2 in seq:
                idx1, idx2 = seq.index(s1), seq.index(s2)
                if abs(idx1 - idx2) == 1:
                    valid_routes.append(r.id())
        
        if not current_route:
            current_route = valid_routes[0] if valid_routes else "Unknown"
            current_leg_stops = [s1, s2]
        else:
            if current_route in valid_routes:
                current_leg_stops.append(s2)
            else:
                c_route_legs.append((current_route, current_leg_stops))
                current_route = valid_routes[0] if valid_routes else "Unknown"
                current_leg_stops = [s1, s2]
                
    if current_route:
        c_route_legs.append((current_route, current_leg_stops))

    c_xs, c_ys = [], []
    for stop_id in candidate_stops:
        s = next((st for st in stops if st.id() == stop_id), None)
        if s:
            c_xs.append(s.coord().lat())
            c_ys.append(s.coord().lon())
            
    if c_xs and c_ys:
        ax.plot(c_xs, c_ys, color='#ff7f0e', linewidth=8, alpha=0.5, 
                label="Candidate Trip (Hành trình OD)", zorder=6, linestyle='-')

    candidate_transfer_points = []
    c_leg_strs = []
    for leg_idx, (r_id, leg_stops) in enumerate(c_route_legs):
        c_leg_strs.append(f"{r_id} ({leg_stops[0]} -> {leg_stops[-1]})")
        if leg_idx < len(c_route_legs) - 1:
            transfer_stop_id = leg_stops[-1]
            t_s = next((st for st in stops if st.id() == transfer_stop_id), None)
            if t_s:
                candidate_transfer_points.append((t_s.coord().lat(), t_s.coord().lon()))
                
    for tx, ty in candidate_transfer_points:
        ax.scatter([tx], [ty], color='#ff7f0e', s=450, edgecolor='black', zorder=13, marker='*')

    candidate_info_str = "Candidate Trip: " + " => ".join(c_leg_strs)

    trip_styles = [(route_colors[0], '-', 6, 'Trip 1 (1 leg) - Bám phải/dưới', -0.0003), 
                   (route_colors[1], '-', 6, 'Trip 2 (2 legs) - Bám trái/trên', 0.0003)]
                   
    trip_info_texts = []
    
    for trip_idx, trip in enumerate(trips):
        color, ls, lw, label_name, offset_val = trip_styles[trip_idx % len(trip_styles)]
        
        trip_leg_strs = []
        transfer_points = []
        leg_offsets = []
        
        for leg_idx, leg in enumerate(trip.legs):
            r = next((route for route in routes if route.id() == leg.route_id), None)
            if not r: 
                leg_offsets.append((0, 0))
                continue
            
            seq = r.stops_seq()
            trip_leg_strs.append(f"{leg.route_id} ({leg.board_stop_id} -> {leg.alight_stop_id})")
            
            try:
                idx1 = seq.index(leg.board_stop_id)
                idx2 = seq.index(leg.alight_stop_id)
                if idx1 > idx2: idx1, idx2 = idx2, idx1
                leg_stops = seq[idx1:idx2+1]
                
                orig_xs, orig_ys = [], []
                for sid in leg_stops:
                    st = next((st for st in stops if st.id() == sid), None)
                    if st: 
                        orig_xs.append(st.coord().lat())
                        orig_ys.append(st.coord().lon())
                        
                is_vertical = len(orig_xs) > 1 and abs(orig_xs[0] - orig_xs[-1]) < 0.0001
                dx = offset_val if is_vertical else 0
                dy = 0 if is_vertical else offset_val
                leg_offsets.append((dx, dy))
            except ValueError:
                leg_offsets.append((0, 0))
                
        for leg_idx, leg in enumerate(trip.legs):
            r = next((route for route in routes if route.id() == leg.route_id), None)
            if not r: continue
            seq = r.stops_seq()
            try:
                idx1 = seq.index(leg.board_stop_id)
                idx2 = seq.index(leg.alight_stop_id)
                if idx1 > idx2: idx1, idx2 = idx2, idx1
                leg_stops = seq[idx1:idx2+1]
                
                leg_coords = []
                for sid in leg_stops:
                    st = next((st for st in stops if st.id() == sid), None)
                    if st: leg_coords.append(st.coord())
                
                xs, ys = [], []
                dx, dy = leg_offsets[leg_idx]
                
                for j, p in enumerate(leg_coords):
                    px, py = p.lat(), p.lon()
                    
                    if j == 0 and leg_idx > 0:
                        p_dx, p_dy = leg_offsets[leg_idx - 1]
                        xs.append(px + p_dx + dx)
                        ys.append(py + p_dy + dy)
                        transfer_points.append((px + p_dx + dx, py + p_dy + dy))
                    elif j == len(leg_coords) - 1 and leg_idx < len(trip.legs) - 1:
                        n_dx, n_dy = leg_offsets[leg_idx + 1]
                        xs.append(px + dx + n_dx)
                        ys.append(py + dy + n_dy)
                    else:
                        xs.append(px + dx)
                        ys.append(py + dy)

                ax.plot(xs, ys, color=color, linewidth=lw, linestyle=ls, 
                        label=label_name if leg_idx == 0 else "", alpha=0.9, zorder=9)
            except ValueError:
                pass
                
        trip_info_texts.append(f"Trip {trip_idx + 1}: {' => '.join(trip_leg_strs)}")
        
        for tx, ty in transfer_points:
            ax.scatter([tx], [ty], color='gold', s=350, edgecolor='black', zorder=12, marker='*')

    ax.scatter([], [], color='gold', s=150, edgecolor='black', marker='*', label="Điểm chuyển tuyến của Trip Đánh Giá")
    ax.scatter([], [], color='#ff7f0e', s=150, edgecolor='black', marker='*', label="Điểm chuyển tuyến Candidate Trip")

    stops_x = [stop.coord().lat() for stop in stops]
    stops_y = [stop.coord().lon() for stop in stops]
    ax.scatter(stops_x, stops_y, color='black', zorder=7, s=30)
    for stop in stops:
        ax.text(stop.coord().lat(), stop.coord().lon() - 0.00015, stop.id(), 
                fontsize=9, ha='center', va='top', color='black', zorder=10)

    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper left', fontsize=10, bbox_to_anchor=(1, 1))

    case_titles = [
        "Case 1: OD giao với biên Trip",
        "Case 2: OD giao 1 phần với Trip",
        "Case 3: OD nằm hoàn toàn trong Trip",
        "Case 4: OD bao trùm hết Trip",
        "Case 5: Candidate trip kết nối 1 Test Trip và 1 Route khác"
    ]
    ax.set_title(case_titles[case_id-1], fontsize=18, pad=20)
    
    note_text = "Thông tin chi tiết:\n"
    note_text += "\n".join(route_info_texts) + "\n\n"
    note_text += candidate_info_str + "\n"
    note_text += "\n".join(trip_info_texts)
    
    plt.figtext(0.05, 0.02, note_text, fontsize=11, family='monospace',
                bbox=dict(facecolor='lightgrey', alpha=0.5, boxstyle='round,pad=0.5'))

    ax.set_aspect('equal', adjustable='datalim')
    plt.grid(True, linestyle='--', alpha=0.4)
    
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Lưu plot Case {case_id} thành công tại {save_path}")

def main():
    os.makedirs("plot_results", exist_ok=True)
    for i in range(1, 6):
        draw_case(i, f"plot_results/kpi_test_case_v4_{i}.png")

if __name__ == "__main__":
    main()
