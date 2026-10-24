"""Symmetric strategic terrain; decorative variation lives only in the renderer."""
from .map import Tile


def enhance(w):
    cells=w.terrain.cells
    # Three architectural districts, with a mirrored canal and wide armored routes.
    for y in range(12,244):
        for x in range(12,128):
            tile=cells[y][x]
            if 55<=x<=59:tile=Tile.DEEP_WATER
            if 55<=x<=59 and any(abs(y-cross)<=3 for cross in (56,128,200)):tile=Tile.BRIDGE
            # Small blocks leave 16m streets and 12m courtyards between them.
            if 92<=y<=164 and 72<=x<=119:
                lx,ly=(x-72)%16,(y-92)%16
                tile=Tile.ROAD if lx<4 or ly<4 else Tile.BUILDING_INTERIOR if 6<=lx<=10 and 6<=ly<=10 else Tile.GRASS
            if 174<=y<=222 and 72<=x<=112:
                lx,ly=(x-72)%20,(y-174)%20
                tile=Tile.ROAD if lx<4 or ly<4 else Tile.BUILDING_INTERIOR if 7<=lx<=13 and 8<=ly<=13 else Tile.GRASS
            # Continuous east/west routes and side-road junctions fit the MBT footprint.
            if any(abs(y-road)<=2 for road in (56,128,200)) and not 55<=x<=59:tile=Tile.ROAD
            if x in range(40,44) or x in range(86,90):tile=Tile.ROAD
            cells[y][x]=cells[y][255-x]=int(tile)
    # Open deployment precincts, spawn pads and every facility entrance.
    for u in [*w.soldiers.values(),*w.vehicles.values(),*w.facilities.values()]:
        radius=8 if hasattr(u,'kind') else 4
        for y in range(max(0,u.pos.y_cm//400-radius),min(256,u.pos.y_cm//400+radius+1)):
            for x in range(max(0,u.pos.x_cm//400-radius),min(256,u.pos.x_cm//400+radius+1)):
                cells[y][x]=cells[y][255-x]=0
    w.terrain.revision+=1;w.terrain.cache.clear()
