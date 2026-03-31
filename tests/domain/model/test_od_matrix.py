import pytest
from src.domain.model.od_matrix import ODMatrix
from src.domain.model.od_pair import ODPair
from src.domain.model.zone import Zone
from src.domain.model.point import Point

def test_od_matrix_creation():
    z1 = Zone("Z1", [], Point(0,0))
    z2 = Zone("Z2", [], Point(1,1))
    od1 = ODPair("OD1", "Z1", "Z2", 100)
    
    matrix = ODMatrix([od1], [z1, z2])
    
    assert len(matrix.zones()) == 2
    assert len(matrix.od_pairs()) == 1
    assert matrix.get_zone_by_id("Z1") == z1
    assert matrix.get_od_pair_by_id("OD1") == od1
