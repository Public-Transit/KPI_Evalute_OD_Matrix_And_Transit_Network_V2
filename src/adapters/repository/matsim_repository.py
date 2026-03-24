class XMLMatsimRepository(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def get(self, reference) -> Tuple[list[Stop], list[Route], list[Zone], list[ODPair], list[Trip]]:
        pass
