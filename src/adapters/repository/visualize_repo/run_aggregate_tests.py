import os
import sys


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.append(project_root)

from src.adapters.repository.visualize_zone_and_transitnetwork import (
    VisualizeZoneAndTransitNetwork,
)
from tests.domain.service.aggregate.aggregate_fake_repo_support import (
    AGGREGATE_CASES,
    run_aggregate_case,
)


def main():
    visualizer = VisualizeZoneAndTransitNetwork()
    output_dir = os.path.dirname(__file__)

    print("=" * 70)
    print("VISUALIZE AGGREGATE KPI FAKE REPOSITORIES")
    print("=" * 70)

    for case in AGGREGATE_CASES:
        repo = case.repo_factory()
        result = run_aggregate_case(repo)
        save_path = os.path.join(output_dir, case.image_name)

        print(f"\n[{case.case_id}] {case.title}")
        print(
            f" -> Trip count: {result['trip_count']} | Valid trips after filtering: {result['valid_trip_count']}"
        )
        print(
            " -> OD composite score:",
            result["aggregated_kpis"]["composite_kpi"]["score"],
        )

        visualizer.show(
            repo.get_od_matrix(),
            repo.get_transit_network(),
            save_path=save_path,
            title=f"{case.case_id} - {case.title}",
            highlight_stop_ids=case.highlight_stop_ids,
            buffer_radius_m=50.0,
        )

        import matplotlib.pyplot as plt

        plt.close("all")


if __name__ == "__main__":
    main()
