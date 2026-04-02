import os
import sys

from src.adapters.repository.visualize_zone_and_transitnetwork import VisualizeZoneAndTransitNetwork
from src.adapters.repository.fake_repo_demand_case1 import FakeRepoDemandCase1
from src.adapters.repository.fake_repo_demand_case2 import FakeRepoDemandCase2
from src.adapters.repository.fake_repo_demand_case3 import FakeRepoDemandCase3
from src.adapters.repository.fake_repo_demand_case4 import FakeRepoDemandCase4
from src.domain.service.trip_kpi_caculator.total_potential_demand_in_trip import TotalPotentialDemandInTripCalculator
from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator

# Ensure docs/images exists
os.makedirs('docs/images', exist_ok=True)

test_cases = [
    (FakeRepoDemandCase1(), 'docs/images/demand_case1.png', 'Case 1: 1 Leg Trip (Straight)'),
    (FakeRepoDemandCase2(), 'docs/images/demand_case2.png', 'Case 2: 1 Leg Trip (Branching)'),
    (FakeRepoDemandCase3(), 'docs/images/demand_case3.png', 'Case 3: 2 Leg Trip (L-Shape Transfer)'),
    (FakeRepoDemandCase4(), 'docs/images/demand_case4.png', 'Case 4: 2 Leg Trip (Disjoint Legs)')
]

viz = VisualizeZoneAndTransitNetwork()
calculator = TotalPotentialDemandInTripCalculator()
geom_calc = ShapelyGeometryCalculator()

for repo, filename, title in test_cases:
    stops, routes, zones, od_pairs, trips = repo.get()
    od_matrix = repo.get_od_matrix()
    transit_network = repo.get_transit_network()
    
    demand = 0.0
    if len(trips) > 0:
        demand = calculator.calculate(trips[0], transit_network, od_matrix, geom_calc)
        
    full_title = f"{title}\nTotal KPI Potential Demand: {demand}"
    print(f"Generating plot for {title} | Demand: {demand}")
    viz.show(od_matrix, transit_network, save_path=filename, title=full_title)

print("All plots generated successfully.")
