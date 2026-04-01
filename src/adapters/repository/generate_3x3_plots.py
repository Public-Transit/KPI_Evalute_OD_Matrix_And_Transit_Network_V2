import os
from src.adapters.repository.fake_repo_grid_3x3 import FakeRepoGrid3x3
from src.adapters.repository.visualize_zone_and_transitnetwork import VisualizeZoneAndTransitNetwork

def main():
    repo = FakeRepoGrid3x3(seed=68)
    
    stops, routes, zones, od_pairs, trips = repo.get()
    od_matrix = repo.get_od_matrix()
    transit_network = repo.get_transit_network()
    
    vis = VisualizeZoneAndTransitNetwork()
    
    # Đảm bảo thư mục tồn tại
    os.makedirs("plot_results", exist_ok=True)
    
    print("Sẽ tạo Plot 1: Zones + Routes + Stops (ko OD arrows)")
    vis.show_zones_and_routes(
        od_matrix=od_matrix,
        transit_network=transit_network,
        save_path="plot_results/3x3_routes_stops_only.png",
        title="Bản đồ Mạng lưới Tuyến và Trạm dừng (3x3 Grid)"
    )
    
    print("Sẽ tạo Plot 2: Zones + OD arrows (ko Routes, Stops)")
    vis.show_zones_and_od(
        od_matrix=od_matrix,
        save_path="plot_results/3x3_od_demand_only.png",
        title="Bản đồ Nhu cầu OD (Lưu lượng di chuyển)"
    )

if __name__ == "__main__":
    main()
