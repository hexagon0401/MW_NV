import pytest
from engine.map import alpha_terrain, Tile
from engine.state import WorldState


def test_bounds_walls_and_facilities():
    t = alpha_terrain()
    assert t.tile(6400,2000) == Tile.WALL
    assert not t.passable(6400,2000)
    assert t.passable(6400,6400)
    assert not t.passable(12800,0)
    with pytest.raises(ValueError, match='OUT_OF_BOUNDS'):
        t.tile(-1,0)
    assert len(WorldState().facilities) == 2
