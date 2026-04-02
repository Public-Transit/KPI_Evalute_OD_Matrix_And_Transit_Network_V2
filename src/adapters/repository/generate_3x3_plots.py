import os

from src.adapters.repository.fake_repo_grid_3x3 import FakeRepoGrid3x3
from src.adapters.repository.visualize_zone_and_transitnetwork import VisualizeZoneAndTransitNetwork


def main():
    repo = FakeRepoGrid3x3()
    od_matrix = repo.get_od_matrix()
    transit_network = repo.get_transit_network()

    visualizer = VisualizeZoneAndTransitNetwork()
    os.makedirs("plot_results", exist_ok=True)

    print("Generating placeholder network plot: routes and stops")
    visualizer.show_zones_and_routes(
        od_matrix=od_matrix,
        transit_network=transit_network,
        save_path="plot_results/placeholder_routes_stops.png",
        title="Placeholder Network: Routes and Stops",
    )

    print("Generating placeholder network plot: OD demand")
    visualizer.show_zones_and_od(
        od_matrix=od_matrix,
        save_path="plot_results/placeholder_od_demand.png",
        title="Placeholder Network: OD Demand",
    )


if __name__ == "__main__":
    main()
