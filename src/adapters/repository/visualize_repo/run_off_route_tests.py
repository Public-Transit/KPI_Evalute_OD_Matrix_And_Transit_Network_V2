import os
import sys

# Đảm bảo có thể import từ src (script nằm ở src/adapters/repository/visualize_repo)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.append(project_root)

from src.adapters.repository.fake_repo_off1 import FakeRepoOff1
from src.adapters.repository.fake_repo_off2 import FakeRepoOff2
from src.adapters.repository.visualize_zone_and_transitnetwork import VisualizeZoneAndTransitNetwork

from src.domain.service.routing import CombinedRoutingEngine
from src.domain.service.filter import MinDistanceCandidateTripFilterV2
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator

def main():
    os.makedirs('off_route_plots', exist_ok=True)
    visualizer = VisualizeZoneAndTransitNetwork()
    calc = ShapelyGeometryCalculator()
    routing_engine = CombinedRoutingEngine()
    filter_engine = MinDistanceCandidateTripFilterV2()

    repos = [
        ("Off-Route Case 1 (Mid-Edge Stops)", FakeRepoOff1()),
        ("Off-Route Case 2 (Off-Line Drift Stops)", FakeRepoOff2())
    ]
    
    print("=" * 70)
    print("KIỂM TRA TRẠM NẰM NGOÀI ĐỈNH TUYẾN (OFF-ROUTE/PROJECTION)")
    print("=" * 70)

    for name, repo in repos:
        print(f"\n>>> [{name}]")
        od_matrix = repo.get_od_matrix()
        transit_network = repo.get_transit_network()
        
        od_pair = repo.od_pairs[0]
        raw_candidates = routing_engine.find_candidate_trips_for_od_pair(od_pair, od_matrix, transit_network, calc)
        
        file_name = f"off_route_plots/plot_off_route_case_{name.split(' (')[0][-1]}.png"
        visualizer.show(od_matrix, transit_network, save_path=file_name)
        
        if not raw_candidates:
            print("  Không tìm thấy CandidateTrip nào!")
            continue
            
        filtered_trip = filter_engine.filter(od_pair, od_matrix, transit_network, raw_candidates[0], calc)
        
        if filtered_trip:
            print(f"  Thành công! Định tuyến hoạt động bình thường kể cả khi trạm không nằm trên đỉnh Route.")
            for idx, leg in enumerate(filtered_trip.legs):
                print(f"   + Chặng {idx+1} [Tuyển '{leg.route_id}']: Lên tại '{leg.board_stop_id}' ---> Xuống tại '{leg.alight_stop_id}'")
                
                # In thêm khoảng cách tuyến thực tế đã dùng Project/Substring
                route = transit_network.get_route_by_id(leg.route_id)
                bs = transit_network.get_stop_by_id(leg.board_stop_id)
                as_ = transit_network.get_stop_by_id(leg.alight_stop_id)
                dist = calc.calc_distance_between_two_stops_in_route(route, bs, as_)
                print(f"     -> Khoảng cách xe chạy (Route string distance): {dist:.2f} m")
        else:
            print("  Lỗi: Bộ lọc không thể chốt được Trip hợp lệ.")

        import matplotlib.pyplot as plt
        plt.close('all')

if __name__ == '__main__':
    main()
