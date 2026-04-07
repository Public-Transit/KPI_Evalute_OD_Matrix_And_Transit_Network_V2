from src.domain.model.od_pair import ODPair
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.transit_network import TransitNetwork
from src.domain.model.routing_result import ODRoutingResultV2, EvaluatedRoutingOption
from src.domain.port import IGeometryCalculator
from src.domain.model.trip import CandidateTrip, Trip
from src.domain.service.routing import AbstractRouting
from src.domain.service.filter import AbstractCandidateTripFilterV2

class GenerateODRoutingResultService:
    def __init__(self, routing_method: AbstractRouting, candidate_trip_filter: AbstractCandidateTripFilterV2):
        self._routing_method = routing_method
        self._candidate_trip_filter = candidate_trip_filter

    def generate_od_routing_result(self,od_matrix: ODMatrix, transit_network: TransitNetwork, geometry_calculator: IGeometryCalculator) -> list[ODRoutingResultV2]:
        
        list_od_routing_results: list[ODRoutingResultV2] = []

        for od_pair in od_matrix.od_pairs():

            list_evaluated_routing_options: list[EvaluatedRoutingOption] = []

            list_candidate_trips: list[CandidateTrip] = self._routing_method.find_candidate_trips_for_od_pair(od_pair, od_matrix, transit_network, geometry_calculator)
            
            for candidate_trip in list_candidate_trips:

                representative_trip: Trip = self._candidate_trip_filter.filter(od_pair, od_matrix, transit_network, candidate_trip, geometry_calculator)
                
                list_evaluated_routing_options.append(EvaluatedRoutingOption(candidate_trip, representative_trip))
            
            list_od_routing_results.append(ODRoutingResultV2(od_pair.id(), list_evaluated_routing_options))

        return list_od_routing_results
