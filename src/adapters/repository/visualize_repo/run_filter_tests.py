import os
import sys

# Đảm bảo có thể import từ src (script nằm ở src/adapters/repository/visualize_repo)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.append(project_root)

from src.adapters.repository.fake_repo_f1 import FakeRepoF1
from src.adapters.repository.fake_repo_f2 import FakeRepoF2
from src.adapters.repository.fake_repo_f3 import FakeRepoF3
from src.adapters.repository.fake_repo_f4 import FakeRepoF4
from src.adapters.repository.fake_repo_f5 import FakeRepoF5
from src.adapters.repository.visualize_zone_and_transitnetwork import VisualizeZoneAndTransitNetwork

from src.domain.service.routing import CombinedRoutingEngine
from src.domain.service.filter_v2 import MinDistanceCandidateTripFilterV2
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator

def main():

    visualizer = VisualizeZoneAndTransitNetwork()
    calc = ShapelyGeometryCalculator()
    routing_engine = CombinedRoutingEngine()
    filter_engine = MinDistanceCandidateTripFilterV2()

    repos = [
        ("Filter Case 1 (Access Distance Priority)", FakeRepoF1()),
        ("Filter Case 2 (Symmetry Tie-Breaker)", FakeRepoF2()),
        ("Filter Case 3 (Transfer Optimization)", FakeRepoF3()),
        ("Filter Case 4 (O/D Priority Selection)", FakeRepoF4()),
        ("Filter Case 5 (Comprehensive Mesh)", FakeRepoF5())
    ]
    
    print("=" * 70)
    print("KIỂM TRA BỘ LỌC CHỌN TRẠM & XUẤT ẢNH (FILTER V2)")
    print("=" * 70)

    for name, repo in repos:
        print(f"\n>>> [{name}]")
        od_matrix = repo.get_od_matrix()
        transit_network = repo.get_transit_network()
        
        # 1. Định tuyến lấy Candidate Trips
        od_pair = repo.od_pairs[0] # Test suite này chỉ dùng 1 cặp OD
        raw_candidates = routing_engine.find_candidate_trips_for_od_pair(od_pair, od_matrix, transit_network, calc)
        
        # Vẽ biểu đồ ban đầu (hiện mạng lưới candidate)
        file_name = f"src/adapters/repository/visualize_repo//plot_filter_case_{name.split(' (')[0][-1]}.png"
        visualizer.show(od_matrix, transit_network, save_path=file_name)
        
        if not raw_candidates:
            print("  Không tìm thấy CandidateTrip nào!")
            continue
            
        # 2. Lọc Trip thực tế dựa vào filter_v2.py
        # Lưu ý: script test chỉ lấy Candidate đầu tiên để filter thử
        filtered_trip = filter_engine.filter(od_pair, od_matrix, transit_network, raw_candidates[0], calc)
        
        if filtered_trip:
            print(f"  Thành công! Bộ lọc rốt cuộc đã CHỌN HÀNH TRÌNH SAU:")
            # In ra các leg
            for idx, leg in enumerate(filtered_trip.legs):
                print(f"   + Chặng {idx+1} [Tuyển '{leg.route_id}']: Lên tại '{leg.board_stop_id}' ---> Xuống tại '{leg.alight_stop_id}'")
        else:
            print("  Lỗi: Bộ lọc không thể chốt được Trip hợp lệ.")

        import matplotlib.pyplot as plt
        plt.close('all')

if __name__ == '__main__':
    main()
