from src.adapters.repository.fake_repo_ag_base import FakeRepoAGBase
from src.domain.model.od_pair import ODPair
from src.domain.model.route import Route
from src.domain.model.zone import Zone


class FakeRepoAG4(FakeRepoAGBase):
    """
    AG4 - All Trips Filtered Out
    Trips are valid at trip level but all are filtered out by OD hard thresholds.
    """

    def __init__(self):
        super().__init__()

        self.zones = [
            Zone("Z1", [self.p(0, 0), self.p(200, 0), self.p(200, 200), self.p(0, 200)], self.p(100, 100)),
            Zone(
                "Z2",
                [self.p(400, 0), self.p(600, 0), self.p(600, 200), self.p(400, 200)],
                self.p(500, 100),
            ),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_CENTER_A", 100, 100),
            self.s("S2_CENTER_A", 500, 100),
            self.s("S1_CENTER_B", 100, 100),
            self.s("S2_CENTER_B", 500, 100),
        ]
        self.routes = [
            Route("R_LOW_COVERAGE", [self.p(100, 100), self.p(500, 100)], ["S1_CENTER_A", "S2_CENTER_A"]),
            Route(
                "R_HIGH_CIRCUITY",
                [self.p(100, 100), self.p(100, 500), self.p(500, 500), self.p(500, 100)],
                ["S1_CENTER_B", "S2_CENTER_B"],
            ),
        ]
