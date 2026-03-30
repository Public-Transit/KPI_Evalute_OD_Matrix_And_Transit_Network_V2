import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.append(project_root)

from src.adapters.repository.fake_repo_sc1 import FakeRepoSC1
from src.adapters.repository.fake_repo_sc2 import FakeRepoSC2
from src.adapters.repository.fake_repo_sc3 import FakeRepoSC3
from src.adapters.repository.fake_repo_sc4 import FakeRepoSC4
from src.adapters.repository.visualize_zone_and_transitnetwork import VisualizeZoneAndTransitNetwork


def main():
    visualizer = VisualizeZoneAndTransitNetwork()
    output_dir = os.path.dirname(__file__)

    cases = [
        {
            "title": "Spatial Coverage Case 1 - Center Stop (r=50m)",
            "repo": FakeRepoSC1(),
            "file_name": "plot_spatial_coverage_case_1.png",
            "highlight_stop_ids": ["S1_CENTER", "S2_CENTER"],
            "buffer_radius_m": 50.0,
        },
        {
            "title": "Spatial Coverage Case 2 - Boundary Clipping (r=50m)",
            "repo": FakeRepoSC2(),
            "file_name": "plot_spatial_coverage_case_2.png",
            "highlight_stop_ids": ["S1_EDGE", "S2_CENTER"],
            "buffer_radius_m": 50.0,
        },
        {
            "title": "Spatial Coverage Case 3 - Overlap And Duplicate (r=50m)",
            "repo": FakeRepoSC3(),
            "file_name": "plot_spatial_coverage_case_3.png",
            "highlight_stop_ids": ["S1_CENTER", "S1_DUPLICATE", "S1_NEAR", "S2_CENTER"],
            "buffer_radius_m": 50.0,
        },
        {
            "title": "Spatial Coverage Case 4 - First/Last Leg Only (r=50m)",
            "repo": FakeRepoSC4(),
            "file_name": "plot_spatial_coverage_case_4.png",
            "highlight_stop_ids": ["S1_EDGE", "S2_EDGE"],
            "buffer_radius_m": 50.0,
        },
    ]

    print("=" * 70)
    print("VISUALIZE SPATIAL COVERAGE FAKE REPOSITORIES")
    print("=" * 70)

    for idx, case in enumerate(cases, start=1):
        repo = case["repo"]
        od_matrix = repo.get_od_matrix()
        transit_network = repo.get_transit_network()
        save_path = os.path.join(output_dir, case["file_name"])

        print(f"\n[{idx}] {case['title']}")
        print(f" -> Highlighted stops: {', '.join(case['highlight_stop_ids'])}")
        print(f" -> Buffer radius: {case['buffer_radius_m']} m")

        visualizer.show(
            od_matrix,
            transit_network,
            save_path=save_path,
            title=case["title"],
            highlight_stop_ids=case["highlight_stop_ids"],
            buffer_radius_m=case["buffer_radius_m"],
        )

        import matplotlib.pyplot as plt

        plt.close("all")


if __name__ == "__main__":
    main()
