from src.adapters.repository.fake_repo_ag_base import FakeRepoAGBase
from src.domain.model.od_pair import ODPair
from src.domain.model.route import Route
from src.domain.model.zone import Zone


class FakeRepoAG3(FakeRepoAGBase):
    """
    AG3 - Mixed OD
    A very good direct option coexists with a weaker but still valid transfer option.
    """

    def __init__(self):
        super().__init__()

        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(100, 0), self.p(100, 100), self.p(0, 100)], self.p(50, 50)),
            Zone("Z2", [self.p(300, 0), self.p(400, 0), self.p(400, 100), self.p(300, 100)], self.p(350, 50)),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_DIRECT", 50, 50),
            self.s("S2_DIRECT", 350, 50),
            self.s("S1_EDGE", 20, 20),
            self.s("H_TRANSFER", 20, 200),
            self.s("S2_EDGE", 350, 20),
        ]
        self.routes = [
            Route("R_DIRECT", [self.p(50, 50), self.p(350, 50)], ["S1_DIRECT", "S2_DIRECT"]),
            Route("R_TRANSFER_1", [self.p(20, 20), self.p(20, 200)], ["S1_EDGE", "H_TRANSFER"]),
            Route(
                "R_TRANSFER_2",
                [self.p(20, 200), self.p(350, 200), self.p(350, 20)],
                ["H_TRANSFER", "S2_EDGE"],
            ),
        ]
