from abc import ABC, abstractmethod

from src.domain.model.od_pair import ODPair
from src.domain.model.zone import Zone
from src.domain.model.trip import Trip
from src.domain.model.route import Route
from src.domain.model.stop import Stop
from src.domain.model.point import Point

class AbstractRepository(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def get(self, reference) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        pass

    

    