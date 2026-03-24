import pytest
from src.domain.model.od_pair import ODPair

def test_od_pair_creation():
    pair = ODPair("OD1", "OriginZ", "DestZ", 100)
    assert pair.id() == "OD1"
    assert pair.origin_zone_id() == "OriginZ"
    assert pair.destination_zone_id() == "DestZ"
    assert pair.demand() == 100
