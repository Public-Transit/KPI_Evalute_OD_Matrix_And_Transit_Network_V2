import os

from src.adapters.repository.fake_repo_grid_3x3 import FakeRepoGrid3x3
from src.adapters.repository.visualize_zone_and_transitnetwork import VisualizeZoneAndTransitNetwork


def main():
    repo = FakeRepoGrid3x3()
    visualizer = VisualizeZoneAndTransitNetwork()
    os.makedirs("plot_results", exist_ok=True)

    print("Generating repository-driven visualization set")
    output_paths = visualizer.show_repository_views(
        repo=repo,
        save_dir="plot_results",
        file_prefix="placeholder",
        title_prefix="Placeholder Network",
        top_n_od_pairs=None,
        label_all_stops=True,
    )
    for view_name, path in output_paths.items():
        print(f"{view_name}: {path}")


if __name__ == "__main__":
    main()
