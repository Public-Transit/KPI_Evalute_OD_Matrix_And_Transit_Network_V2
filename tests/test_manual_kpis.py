import os
import sys

# Đảm bảo có thể import từ src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(project_root)

from src.adapters.repository.fake_repo_c1 import FakeRepoC1
from src.adapters.repository.fake_repo_c2 import FakeRepoC2
from src.adapters.repository.fake_repo_t1 import FakeRepoT1
from src.adapters.repository.fake_repo_t2 import FakeRepoT2

from src.domain.service.routing import CombinedRoutingEngine
from src.domain.service.filter_v2 import MinDistanceCandidateTripFilterV2
from src.domain.service.kpi_caculator.circuity_kpi import CircuityIndexCalculator
from src.domain.service.kpi_caculator.transfer_kpi import TransferRateCalculator
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator
from src.domain.model.routing_result_v2 import EvaluatedRoutingOption

def run_tests():
    calc = ShapelyGeometryCalculator()
    routing_engine = CombinedRoutingEngine()
    filter_engine = MinDistanceCandidateTripFilterV2()
    circ_kpi = CircuityIndexCalculator() # Không cần repo nữa vì đã cập nhật code.
    trans_kpi = TransferRateCalculator()

    repos_to_test = [
        ("C1: Straight Line (Circuity KPI)", FakeRepoC1(), circ_kpi),
        ("C2: U-Turn Detour (Circuity KPI)", FakeRepoC2(), circ_kpi),
        ("T1: Direct route (Transfer KPI)", FakeRepoT1(), trans_kpi),
        ("T2: 1-Transfer route (Transfer KPI)", FakeRepoT2(), trans_kpi),
    ]

    print("================== KẾT QUẢ TEST CIRCUITY VÀ TRANSFER ==================")
    
    for name, repo, kpi_engine in repos_to_test:
        print(f"\n[+] Chạy thử nghiệm: {name}")
        od_matrix = repo.get_od_matrix()
        transit_network = repo.get_transit_network()
        od_pair = repo.od_pairs[0]
        
        # 1. Định tuyến
        candidates = routing_engine.find_candidate_trips_for_od_pair(od_pair, od_matrix, transit_network, calc)
        if not candidates:
            print("  [-] Không tìm thấy lộ trình!")
            continue
            
        # 2. Lọc tuyến tối ưu nhất
        filtered_trip = filter_engine.filter(od_pair, od_matrix, transit_network, candidates[0], calc)
        if not filtered_trip:
            print("  [-] Bị loại bởi filter!")
            continue
            
        # 3. Build EvaluatedRoutingOption giả để quăng vào KPI Calculator
        eval_option = EvaluatedRoutingOption(candidate_trip=candidates[0], representative_trip=filtered_trip)
        
        # 4. Tính KPI
        try:
            # Sửa đổi: kwargs parameter có transit_network và geometry_calculator cho Circuity
            result = kpi_engine.calculate(eval_option, transit_network=transit_network, geometry_calculator=calc)
            print(f"  => Kết quả: {result}")
        except Exception as e:
            print(f"  [-] Lỗi tính KPI: {e}")

if __name__ == "__main__":
    run_tests()
