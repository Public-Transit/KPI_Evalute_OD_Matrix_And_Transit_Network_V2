from src.adapters.repository.fake_repo_ag_base import FakeRepoAGBase
from src.domain.model.od_pair import ODPair
from src.domain.model.route import Route
from src.domain.model.zone import Zone


class FakeRepoAG2(FakeRepoAGBase):
    """
    AG2 - Weak But Valid OD
    Only one-transfer option exists. Coverage is lower than AG1 but still valid.
    """

    def __init__(self):
        super().__init__()

        self.zones = [
            Zone(
                "Z1",
                [self.p(0, 0), self.p(145, 0), self.p(145, 145), self.p(0, 145)],
                self.p(72.5, 72.5),
            ),
            Zone(
                "Z2",
                [self.p(300, 227), self.p(445, 227), self.p(445, 372), self.p(300, 372)],
                self.p(372.5, 299.5),
            ),
        ]
        self.od_pairs = [ODPair("OD1", "Z1", "Z2", 100)]
        self.stops = [
            self.s("S1_ORIGIN", 73, 73),
            self.s("H_TRANSFER", 73, 300),
            self.s("S2_DEST", 373, 300),
        ]
        self.routes = [
            Route("R_FEEDER", [self.p(73, 73), self.p(73, 300)], ["S1_ORIGIN", "H_TRANSFER"]),
            Route("R_TRUNK", [self.p(73, 300), self.p(373, 300)], ["H_TRANSFER", "S2_DEST"]),
        ]
