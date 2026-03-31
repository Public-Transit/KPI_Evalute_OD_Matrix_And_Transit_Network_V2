from src.domain.model.od_pair import ODPair
from src.domain.model.zone import Zone

class ODMatrix:
    def __init__(self, od_pairs: list[ODPair], zones: list[Zone]):
        self._od_pairs = od_pairs
        self._zones = zones
        
        # Hash maps for fast lookup
        self._zone_map = {zone.id(): zone for zone in zones} 
        self._od_pair_map = {od_pair.id(): od_pair for od_pair in od_pairs}



    def od_pairs(self) -> list[ODPair]:
        return self._od_pairs
    
    def zones(self) -> list[Zone]:
        return self._zones
        
    def get_zone_by_id(self, zone_id: str) -> Zone:
        return self._zone_map.get(zone_id)
    
    def get_od_pair_by_id(self, od_pair_id: str) -> ODPair:
        return self._od_pair_map.get(od_pair_id)