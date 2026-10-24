"""Non-weaponized carriers: footprint-aware routes and distance-based fuel."""
from math import hypot,ceil
from .map import Terrain,Tile
from .orders import OrderError
from .pathfinding import find_path
from .types import WorldPos


class FootprintTerrain(Terrain):
    def __init__(self,terrain,footprint):
        self.__dict__.update(terrain.__dict__)
        self.cache={}
        self.footprint=footprint

    def passable(self,x,y,vehicle=True):
        half_w,half_h=[v//2 for v in self.footprint]
        left,right=x-half_w,x+half_w-1
        top,bottom=y-half_h,y+half_h-1
        if not self.inside(left,top) or not self.inside(right,bottom):
            return False
        return all(self.cells[row][col] in (0,1,7,8) for row in range(top//400,bottom//400+1) for col in range(left//400,right//400+1))


def move_vehicle(w,key,v,destination):
    spec=w.vehicle_specs[v.type_id]
    if v.fuel<=0:
        v.task_state='NO_FUEL';w.emit('VEHICLE_OUT_OF_FUEL',unit=v.id)
        raise OrderError('NO_FUEL')
    if v.task_state in ('WAITING_PASSENGERS','UNLOADING'):
        raise OrderError('ILLEGAL_STATE')
    if not hasattr(w,'vehicle_motions'):
        w.vehicle_motions={}
    terrain=FootprintTerrain(w.terrain,spec['footprint_cm'])
    if key not in w.vehicle_motions:
        v.task_state='PATHING'
        route=find_path(terrain,(v.pos.x_cm,v.pos.y_cm),destination,True)
        w.vehicle_motions[key]=dict(route=route,x=float(v.pos.x_cm),y=float(v.pos.y_cm))
    motion=w.vehicle_motions[key]
    factor=1 if w.terrain.tile(v.pos.x_cm,v.pos.y_cm) in (Tile.ROAD,Tile.BRIDGE) else spec['grass_factor']
    budget=min(spec['speed_mps']*20*factor,v.fuel/spec['fuel_per_100m']*10000)
    v.task_state='MOVING'
    while motion['route'] and budget>1e-8:
        x,y=motion['x'],motion['y'];tx,ty=motion['route'][0]
        distance=hypot(tx-x,ty-y);amount=min(distance,budget)
        nx,ny=(tx,ty) if amount>=distance else (x+(tx-x)*amount/distance,y+(ty-y)*amount/distance)
        candidate=WorldPos(round(nx),round(ny))
        if not terrain.segment_clear((v.pos.x_cm,v.pos.y_cm),(candidate.x_cm,candidate.y_cm),True):
            v.task_state='BLOCKED';raise OrderError('BLOCKED')
        for other in w.vehicles.values():
            fp=w.vehicle_specs[other.type_id]['footprint_cm']
            if other.id!=v.id and abs(other.pos.x_cm-candidate.x_cm)<(fp[0]+spec['footprint_cm'][0])/2 and abs(other.pos.y_cm-candidate.y_cm)<(fp[1]+spec['footprint_cm'][1])/2:
                v.task_state='BLOCKED';raise OrderError('BLOCKED')
        v.pos=candidate;motion['x'],motion['y']=nx,ny
        v.fuel=max(0,v.fuel-amount/10000*spec['fuel_per_100m'])
        if v.fuel<1e-9:v.fuel=0
        budget-=amount
        if amount>=distance:motion['route'].pop(0)
        for id in v.passenger_ids:w.soldiers[id].pos=v.pos
        w.emit('UNIT_MOVED',unit=v.id,x_cm=v.pos.x_cm,y_cm=v.pos.y_cm)
    if not motion['route']:
        v.task_state='ARRIVED';w.emit('UNIT_ARRIVED',unit=v.id)
        return True
    return False
