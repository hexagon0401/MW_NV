import pytest
from engine.map import Terrain, Tile
from engine.orders import OrderError
from engine.pathfinding import find_path


def test_wall_detour_cache_invalidation_and_unreachable():
    t = Terrain(32,32)
    for row in range(7):
        t.set_tile(4,row,Tile.WALL)
    route = find_path(t,(200,200),(3000,200))
    assert max(y for x,y in route) >= 2800
    assert route == find_path(t,(200,200),(3000,200))
    points = [(200,200)]+route
    assert all(t.segment_clear(a,b) for a,b in zip(points,points[1:]))
    t.set_tile(4,7,Tile.WALL)
    assert not t.cache
    with pytest.raises(OrderError,match='PATH_NOT_FOUND'):
        find_path(t,(200,200),(3000,200))
