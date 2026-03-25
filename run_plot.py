import os
import sys

# Đảm bảo có thể import từ src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# from src.adapters.repository.fake_reapository import FakeRepository
from src.adapters.repository.complex_test_repository import ComplexTestRepository
from src.adapters.repository.visualize_zone_and_transitnetwork import VisualizeZoneAndTransitNetwork

def main():
    repo = ComplexTestRepository()
    od_matrix = repo.get_od_matrix()
    transit_network = repo.get_transit_network()
    
    visualizer = VisualizeZoneAndTransitNetwork()
    print("Đang tạo biểu đồ đồ thị...")
    visualizer.show(od_matrix, transit_network, save_path="get_plot.png")
    
if __name__ == "__main__":
    main()
