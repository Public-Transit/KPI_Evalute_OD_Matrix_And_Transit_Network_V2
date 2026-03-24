import pytest
from src.domain.model.stop import Stop
from src.domain.model.point import Point

def test_stop_creation():
    s = Stop("S01", 21.0, 105.0)
    assert s.id() == "S01"
    assert s.lat() == 21.0
    assert s.lon() == 105.0
    assert s.coord().lat() == 21.0
