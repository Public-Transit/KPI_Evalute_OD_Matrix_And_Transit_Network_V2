class ODPair:
    def __init__(self, od_pair_id: str, origin_zone_id: str, destination_zone_id: str, demand: float):
        self._id = od_pair_id
        self._origin_zone_id = origin_zone_id
        self._destination_zone_id = destination_zone_id
        self._demand = demand

    def id(self) -> str:
        return self._id

    def origin_zone_id(self) -> str:
        return self._origin_zone_id
    
    def destination_zone_id(self) -> str:
        return self._destination_zone_id
    
    def demand(self) -> float:
        return self._demand