from abc import ABC, abstractmethod

from src.domain.model.od_pair import ODPair
from src.domain.model.zone import Zone
from src.domain.model.route import Route
from src.domain.model.stop import Stop

class AbstractRepository(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def get(self, reference) -> tuple[list[Stop], list[Route], list[Zone], list[ODPair]]:
        pass

    

    