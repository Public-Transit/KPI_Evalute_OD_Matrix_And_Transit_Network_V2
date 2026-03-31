from src.domain.model.stop import Stop
from src.domain.model.route import Route

class TransitNetwork:
    def __init__(self, stops: list[Stop], routes: list[Route]):
        self._stops = stops
        self._routes = routes
        
        # Hash maps cho mục đích tìm kiếm O(1)
        self._stop_map = {stop.id(): stop for stop in stops}
        self._route_map = {route.id(): route for route in routes}

    def stops(self) -> list[Stop]:
        return self._stops
    
    def routes(self) -> list[Route]:
        return self._routes
        
    def get_stop_by_id(self, stop_id: str) -> Stop:
        return self._stop_map.get(stop_id)
        
    def get_route_by_id(self, route_id: str) -> Route:
        return self._route_map.get(route_id)
