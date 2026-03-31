import os
import sys

# Đảm bảo có thể import từ src (script nằm ở src/adapters/repository/visualize_repo)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.append(project_root)

from src.adapters.repository.fake_repo_l1 import FakeRepoL1
from src.adapters.repository.fake_repo_l2 import FakeRepoL2
from src.adapters.repository.fake_repo_l3 import FakeRepoL3
from src.adapters.repository.fake_repo_l4 import FakeRepoL4
from src.adapters.repository.fake_repo_l5 import FakeRepoL5
from src.adapters.repository.visualize_zone_and_transitnetwork import VisualizeZoneAndTransitNetwork

from src.domain.service.routing import CombinedRoutingEngine
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator

def main():
    visualizer = VisualizeZoneAndTransitNetwork()
    calc = ShapelyGeometryCalculator()
    routing_engine = CombinedRoutingEngine()

    repos = [
        ("Level 1", FakeRepoL1()),
        ("Level 2", FakeRepoL2()),
        ("Level 3", FakeRepoL3()),
        ("Level 4", FakeRepoL4()),
        ("Level 5", FakeRepoL5())
    ]
    
    print("=" * 50)
    print("KIỂM TRA CÁC MỨC ĐỘ MẠNG LƯỚI & XUẤT ẢNH")
    print("=" * 50)

    for name, repo in repos:
        print(f"\n[{name}]")
        od_matrix = repo.get_od_matrix()
        transit_network = repo.get_transit_network()
        
        # Test routing algorithm để xem số lượng 
        for od_pair in repo.od_pairs:
            trips = routing_engine.find_candidate_trips_for_od_pair(od_pair, od_matrix, transit_network, calc)
            print(f" -> Cặp {od_pair.id()} ({od_pair.origin_zone_id()} đến {od_pair.destination_zone_id()}): "
                  f"Đã tìm thấy {len(trips)} lựa chọn đi qua đường (candidate trips).")
            for t in trips:
                leg_str = " + ".join([leg.route_id for leg in t.candidate_legs])
                print(f"    * Tuyến đi: {leg_str}")
            
        file_name = f"src/adapters/repository/visualize_repo/plot_{name.replace(' ', '_').lower()}.png"
        visualizer.show(od_matrix, transit_network, save_path=file_name)
        # Fix cho pyplot matplotlib dồn RAM khi lặp nhiều lần
        import matplotlib.pyplot as plt
        plt.close('all')

if __name__ == '__main__':      
    main()
