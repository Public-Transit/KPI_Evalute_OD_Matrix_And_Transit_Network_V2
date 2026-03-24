from src.domain.model.point import Point

class Stop:
    def __init__(self, stop_id: str, lat: float, lon: float):
        self._id = stop_id
        self._lat = lat
        self._lon = lon
        self._coord = Point(lat, lon)

    def id(self) -> str:
        return self._id
    
    def lat(self) -> float:
        return self._lat
    
    def lon(self) -> float:
        return self._lon
    
    def coord(self) -> Point:
        return self._coord

    def update_stops(self, new_stops: list[str]):
        self._stops = new_stops