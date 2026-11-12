"""Mirrored navigation geometry with organic woods and three readable districts."""
from math import sin,hypot
from .map import Tile

MAP_ID='river-districts'
MAP_VERSION='2'

def enhance(w):
    cells=w.terrain.cells;n=len(cells);half=n//2
    def stamp(x,y,t):
        if 0<=y<n and 0<=x<half:cells[y][x]=cells[y][n-1-x]=int(t)
    # Coherent broad woodland masses, not isolated random cells or repeating rectangles.
    woods=[(27,35,18,20),(90,30,22,13),(108,77,17,12),(24,92,14,19),(76,171,20,13),(26,226,21,14),(115,237,16,12)]
    for y in range(n):
        for x in range(half):
            score=max((1-((x-cx)/rx)**2-((y-cy)/ry)**2 for cx,cy,rx,ry in woods))
            edge=.16*sin(x*.43+y*.18)+.11*sin(y*.51-x*.12)
            stamp(x,y,Tile.FOREST if score+edge>.12 else Tile.GRASS)
    # Meandering twin canals; bridge and road construction below resolves every crossing.
    for y in range(12,244):
        center=57+round(3*sin(y/31)+sin(y/11))
        for x in range(center-3,center+4):stamp(x,y,Tile.DEEP_WATER if abs(x-center)<=1 else Tile.SHALLOW_WATER)
    def rect(x,y,width,height,t):
        for yy in range(y,y+height):
            for xx in range(x,x+width):stamp(xx,yy,t)
    # Individual connected footprints; courtyards and streets are deliberately generous.
    for x,y,width,height in [(76,97,6,9),(94,100,9,6),(111,95,6,8),(80,116,7,6),(102,116,5,7),(113,140,6,8),(92,145,9,6),(75,141,7,10),(79,158,8,5),(105,159,10,5)]:rect(x,y,width,height,Tile.BUILDING_INTERIOR)
    for x,y,width,height in [(76,181,11,6),(97,178,8,9),(111,187,7,6),(77,212,12,6),(101,213,14,7)]:rect(x,y,width,height,Tile.BUILDING_INTERIOR)
    for x,y in [(92,188),(116,210),(72,221)]:rect(x,y,2,2,Tile.OBSTACLE)
    def road(points,width=5):
        radius=width/2
        for (ax,ay),(bx,by) in zip(points,points[1:]):
            length=max(1,round(hypot(bx-ax,by-ay)*2))
            for i in range(length+1):
                cx=ax+(bx-ax)*i/length;cy=ay+(by-ay)*i/length
                for yy in range(int(cy-radius)-1,int(cy+radius)+2):
                    for xx in range(int(cx-radius)-1,int(cx+radius)+2):
                        if 0<=yy<n and 0<=xx<half and hypot(xx-cx,yy-cy)<=radius:
                            stamp(xx,yy,Tile.BRIDGE if cells[yy][xx] in (5,6,7) else Tile.ROAD)
    # At least 20m along major corridors; mirrored distances/start pads remain fair.
    for y in (56,128,200):road([(16,y),(128,y)],7)
    road([(39,18),(39,67),(45,101),(42,152),(36,191),(42,238)],6)
    road([(86,48),(87,82),(69,100),(69,151),(88,174),(88,234)],5)
    road([(69,91),(118,91),(122,128),(122,171),(88,171)],5)
    road([(69,155),(94,155),(94,128)],5)
    road([(69,175),(120,175),(123,224),(73,224),(69,200)],5)
    # Site access and spawn pads are circular, avoiding visible square cut-outs in woods.
    for u in [*w.soldiers.values(),*w.vehicles.values(),*w.facilities.values()]:
        cx=u.pos.x_cm//400;cy=u.pos.y_cm//400
        if cx>=half:cx=n-1-cx
        radius=9 if hasattr(u,'kind') else 4
        for y in range(max(0,cy-radius),min(n,cy+radius+1)):
            for x in range(max(0,cx-radius),min(half,cx+radius+1)):
                if hypot(x-cx,y-cy)<=radius:stamp(x,y,Tile.GRASS)
    w.map_id=MAP_ID;w.map_version=MAP_VERSION
    w.terrain.revision+=1;w.terrain.cache.clear()
