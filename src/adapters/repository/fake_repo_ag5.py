from src.adapters.repository.fake_repo_ag_base import FakeRepoAGBase
from src.domain.model.od_pair import ODPair
from src.domain.model.route import Route
from src.domain.model.zone import Zone


class FakeRepoAG5(FakeRepoAGBase):
    """
    AG5 - Tie Stability
    Two equally good options and one slightly worse option for the same OD.
    """

    def __init__(self):
        super().__init__()

        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(100, 0), self.p(100, 100), self.p(0, 100)], self.p(50, 50)),
            Zone("Z2", [self.p(300, 0), self.p(400, 0), self.p(400, 100), self.p(300, 100)], self.p(350, 50)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_A", 50, 50),
            self.s("S2_A", 350, 50),
            self.s("S1_B", 50, 50),
            self.s("S2_B", 350, 50),
            self.s("S1_C", 50, 50),
            self.s("S2_C", 350, 50),
        ]
        self.routes = [
            Route("R_BEST_A", [self.p(50, 50), self.p(350, 50)], ["S1_A", "S2_A"]),
            Route("R_BEST_B", [self.p(50, 50), self.p(350, 50)], ["S1_B", "S2_B"]),
            Route(
                "R_WORSE_C",
                [self.p(50, 50), self.p(200, 200), self.p(350, 50)],
                ["S1_C", "S2_C"],
            ),
        ]
