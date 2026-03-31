import os
import sys

# Đảm bảo có thể import từ gốc của dự án
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(project_root)

# Khai báo trực tiếp tất cả các Fake Repos ở đây
from src.adapters.repository.fake_repo_l1 import FakeRepoL1
from src.adapters.repository.fake_repo_l2 import FakeRepoL2
from src.adapters.repository.fake_repo_l3 import FakeRepoL3
from src.adapters.repository.fake_repo_l4 import FakeRepoL4
from src.adapters.repository.fake_repo_l5 import FakeRepoL5

from src.adapters.repository.fake_repo_f1 import FakeRepoF1
from src.adapters.repository.fake_repo_f2 import FakeRepoF2
from src.adapters.repository.fake_repo_f3 import FakeRepoF3
from src.adapters.repository.fake_repo_f4 import FakeRepoF4
from src.adapters.repository.fake_repo_f5 import FakeRepoF5
from src.adapters.repository.fake_repo_f6 import FakeRepoF6

from src.adapters.repository.fake_repo_t1 import FakeRepoT1
from src.adapters.repository.fake_repo_t2 import FakeRepoT2
from src.adapters.repository.fake_repo_t3 import FakeRepoT3
from src.adapters.repository.fake_repo_t5 import FakeRepoT5
from src.adapters.repository.fake_repo_t6 import FakeRepoT6
from src.adapters.repository.fake_repo_t8 import FakeRepoT8
from src.adapters.repository.fake_repo_c1 import FakeRepoC1
from src.adapters.repository.fake_repo_c2 import FakeRepoC2

from src.adapters.repository.fake_repo_off1 import FakeRepoOff1
from src.adapters.repository.fake_repo_off2 import FakeRepoOff2

from src.adapters.repository.fake_repo_master import FakeRepoMaster

from src.adapters.repository.visualize_zone_and_transitnetwork import VisualizeZoneAndTransitNetwork
from src.domain.service.routing import CombinedRoutingEngine
from src.domain.service.filter_v2 import MinDistanceCandidateTripFilterV2, GlobalMinDistanceTripsFilterV2
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator

def main():
    visualizer = VisualizeZoneAndTransitNetwork()
    calc = ShapelyGeometryCalculator()
    routing_engine = CombinedRoutingEngine()
    filter_engine = GlobalMinDistanceTripsFilterV2()

    # =========================================================================
    # DANH SÁCH CÁC TEST CASES ĐỂ CHẠY
    # Bạn có thể Cận (comment out) hoặc Thêm bớt Repo vào mảng này rất dễ dàng
    # =========================================================================
    repos = [
        # --- 1. Định tuyến (Routing Test Suite L1-L5) ---
        ("L1_Routing_Basic", FakeRepoL1()),
        ("L2_Routing_Compete", FakeRepoL2()),
        ("L3_Routing_Transfer", FakeRepoL3()),
        ("L4_Routing_Mixed", FakeRepoL4()),
        ("L5_Routing_SpiderWeb", FakeRepoL5()),
        
        # --- 2. Lọc lộ trình (Filtering Test Suite F1-F6) ---
        ("F1_Filter_AccessPriority", FakeRepoF1()),
        ("F2_Filter_SymmetryTieBreaker", FakeRepoF2()),
        ("F3_Filter_TransferOpt", FakeRepoF3()),
        ("F4_Filter_AccessOverride", FakeRepoF4()),
        ("F6_Filter_TransferTieBreaker", FakeRepoF6()),
        ("F5_Filter_ComplexMesh", FakeRepoF5()),
        
        # --- 3. Chỉ số KPI (Transfer & Circuity) ---
        ("T1_KPI_TransferDirect", FakeRepoT1()),
        ("T2_KPI_Transfer1", FakeRepoT2()),
        ("T3_Filter_AccessPriority_Direct", FakeRepoT3()),
        ("T5_Filter_FullOpt_Transfer", FakeRepoT5()),
        ("T6_Filter_TransferTieBreaker_Complex", FakeRepoT6()),
        ("T8_Filter_MixedCandidates", FakeRepoT8()),
        ("C1_KPI_CircuityStraight", FakeRepoC1()),
        ("C2_KPI_CircuityUTurn", FakeRepoC2()),
        
        # --- 4. Xử lý Trạm sai số Hình học (Off-Route) ---
        ("Off1_Geometry_MidEdge", FakeRepoOff1()),
        ("Off2_Geometry_Drift", FakeRepoOff2()),
        
        # --- 5. Tích hợp Master Case (Mini City) ---
        ("Master_MiniCity", FakeRepoMaster())
    ]
    
    # Tạo thư mục test_plots nằm trong src/adapters/repository/
    save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_plots"))
    os.makedirs(save_dir, exist_ok=True)

    print("=" * 80)
    print(f"BẮT ĐẦU CHẠY {len(repos)} BÀI TEST & XUẤT ẢNH RA THƯ MỤC:")
    print(f" -> {save_dir}")
    print("=" * 80)

    for name, repo in repos:
        print(f"\n>>> Đang xử lý: [{name}]")
        od_matrix = repo.get_od_matrix()
        transit_network = repo.get_transit_network()
        
        # 1. Vẽ toàn bộ mạng của Repo và lưu vào thư mục test_plots
        file_name = os.path.join(save_dir, f"{name}.png")
        visualizer.show(od_matrix, transit_network, save_path=file_name)
        
        # 2. Chạy check logic Tracking & Phân tích
        for od_pair in repo.od_pairs:
            # 2.1 Định Tuyến Dò Tìm
            raw_candidates = routing_engine.find_candidate_trips_for_od_pair(od_pair, od_matrix, transit_network, calc)
            print(f"    [O/D {od_pair.origin_zone_id()} -> {od_pair.destination_zone_id()}]: Tìm thấy {len(raw_candidates)} Candidate Trips hợp quy.")
            
            # 2.2 Lọc Tuyến Tối Ưu (Toàn cục trên mọi Candidates)
            if raw_candidates:
                filtered_trip = filter_engine.filter(od_pair, od_matrix, transit_network, raw_candidates, calc)
                if filtered_trip:
                    print(f"    [+] => Lộ trình lọc (Filter V2) chốt hạ gồm {len(filtered_trip.legs)} chặng:")
                    for idx, leg in enumerate(filtered_trip.legs):
                        print(f"           - {leg.route_id}: Lên trạm '{leg.board_stop_id}' ---> Xuống trạm '{leg.alight_stop_id}'")
                else:
                    print("    [-] => Lỗi: Filter V2 trả về Null cho Candidate này.")
        
        # Xóa cache RAM pyplot sau mỗi bài test để tránh Memory Leak
        import matplotlib.pyplot as plt
        plt.close('all')

    print("\n" + "=" * 80)
    print("✅ Hoàn tất! Tất cả các ảnh đã được tạo.")

if __name__ == '__main__':
    main()
