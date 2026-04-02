from src.adapters.repository.fake_repo_ag_base import FakeRepoAGBase
from src.domain.model.od_pair import ODPair
from src.domain.model.route import Route
from src.domain.model.zone import Zone


class FakeRepoAG1(FakeRepoAGBase):
    """
    AG1 - Excellent Direct OD
    One direct and near-straight route with centered stops and high coverage.
    """

    def __init__(self):
        super().__init__()

        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(100, 0), self.p(100, 100), self.p(0, 100)], self.p(50, 50)),
            Zone("Z2", [self.p(300, 0), self.p(400, 0), self.p(400, 100), self.p(300, 100)], self.p(350, 50)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_CENTER", 50, 50),
            self.s("S2_CENTER", 350, 50),
        ]
        self.routes = [
            Route("R_DIRECT_GOOD", [self.p(50, 50), self.p(350, 50)], ["S1_CENTER", "S2_CENTER"]),
        ]
