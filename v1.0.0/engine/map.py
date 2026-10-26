"""Four metre navigation cells and explicit terrain bounds."""
from enum import IntEnum
from math import ceil, hypot


class Tile(IntEnum):
    GRASS=0
    ROAD=1
    FOREST=2
    WALL=3
    BUILDING_INTERIOR=4
    SHALLOW_WATER=5
    DEEP_WATER=6
    BRIDGE=7
    OBJECTIVE=8
    OBSTACLE=9
    HQ_FLOOR=10


class Terrain:
    def __init__(self, width_m=128, height_m=128):
        self.width_cm, self.height_cm = width_m*100, height_m*100
        self.cols, self.rows = ceil(width_m/4), ceil(height_m/4)
        self.cells = [[int(Tile.GRASS) for _ in range(self.cols)] for _ in range(self.rows)]
        self.revision = 0
        self.cache = {}

    def inside(self, x, y):
        return 0 <= x < self.width_cm and 0 <= y < self.height_cm

    def tile(self, x, y):
        if not self.inside(x,y):
            raise ValueError('OUT_OF_BOUNDS')
        return Tile(self.cells[y//400][x//400])

    def set_tile(self, col, row, tile):
        if not (0 <= col < self.cols and 0 <= row < self.rows):
            raise ValueError('OUT_OF_BOUNDS')
        self.cells[row][col] = int(Tile(tile))
        self.revision += 1
        self.cache.clear()

    def passable(self, x, y, vehicle=False):
        if not self.inside(x,y):
            return False
        allowed = (0,1,7,8) if vehicle else (0,1,2,4,5,7,8,10)
        return self.tile(x,y) in allowed

    def segment_clear(self, start, end, vehicle=False):
        n = max(1, ceil(hypot(end[0]-start[0], end[1]-start[1])/50))
        return all(self.passable(round(start[0]+(end[0]-start[0])*i/n),
                                 round(start[1]+(end[1]-start[1])*i/n),vehicle)
                   for i in range(n+1))


def alpha_terrain():
    terrain = Terrain()
    for x in range(terrain.cols):
        terrain.set_tile(x,16,Tile.ROAD)
    for y in range(4,12):
        terrain.set_tile(16,y,Tile.WALL)
    return terrain
