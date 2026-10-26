"""Deterministic A*, cached until terrain changes. No corner cutting."""
import heapq
from .orders import OrderError


def find_path(terrain, start, end, vehicle=False, offsets=((0,0),)):
    offsets=tuple(offsets)
    def legal(point):return all(terrain.passable(point[0]+dx,point[1]+dy,vehicle) for dx,dy in offsets)
    def clear(a,b):return all(terrain.segment_clear((a[0]+dx,a[1]+dy),(b[0]+dx,b[1]+dy),vehicle) for dx,dy in offsets)
    key = f'{start}:{end}:{vehicle}:{offsets}:{terrain.revision}'
    if key in terrain.cache:
        return list(terrain.cache[key])
    if not legal(start) or not legal(end):
        raise OrderError('PATH_NOT_FOUND')
    if clear(start,end):
        terrain.cache[key] = [end]
        return [end]
    source, goal = (start[0]//400,start[1]//400), (end[0]//400,end[1]//400)
    heap, costs, parent = [(0,source)], {source:0}, {}
    def centre(cell):
        return (min(cell[0]*400+200,terrain.width_cm-1),min(cell[1]*400+200,terrain.height_cm-1))
    while heap:
        _, current = heapq.heappop(heap)
        if current == goal:
            cells = [goal]
            while cells[-1] != source:
                cells.append(parent[cells[-1]])
            route = [centre(c) for c in reversed(cells)] + [end]
            points = [start]+route
            if not all(clear(a,b) for a,b in zip(points,points[1:])):
                raise OrderError('PATH_NOT_FOUND')
            terrain.cache[key] = route
            return list(route)
        x,y = current
        for nxt in ((x-1,y),(x,y-1),(x,y+1),(x+1,y)):
            if not (0 <= nxt[0] < terrain.cols and 0 <= nxt[1] < terrain.rows):
                continue
            if not legal(centre(nxt)) or not clear(centre(current),centre(nxt)):
                continue
            cost = costs[current]+1
            if cost < costs.get(nxt,float('inf')):
                costs[nxt], parent[nxt] = cost,current
                h = abs(nxt[0]-goal[0])+abs(nxt[1]-goal[1])
                heapq.heappush(heap,(cost+h,nxt))
    raise OrderError('PATH_NOT_FOUND')
