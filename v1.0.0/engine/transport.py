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
    if v.type_id=='HEL':
        return fly(w,key,v,destination)
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


def embark(w,key,c):
    from .movement import move
    v=w.vehicles.get(c.target)
    if v is None:raise OrderError('INVALID_TARGET')
    if v.team!=c.team:raise OrderError('FOREIGN_UNIT')
    if v.task_state in ('MOVING','TAKEOFF','LANDING','UNLOADING'):
        raise OrderError('ILLEGAL_STATE')
    ids=w.squads[c.unit].member_ids if c.unit in w.squads else [c.unit]
    if not hasattr(w,'transfers'):w.transfers={}
    if key not in w.transfers:
        if any(i not in w.soldiers or w.soldiers[i].team!=c.team or not w.soldiers[i].alive or w.soldiers[i].carrier_id is not None for i in ids):
            raise OrderError('ILLEGAL_STATE')
        pending=[i for k,t in w.transfers.items() if t['vehicle']==v.id and w.queue.status.get(k) in ('RUNNING','QUEUED') for i in t['remaining']]
        if set(ids)&set(pending):raise OrderError('ILLEGAL_STATE')
        if len(v.passenger_ids)+len(pending)+len(ids)>w.vehicle_specs[v.type_id]['capacity']:
            raise OrderError('NO_CAPACITY')
        w.transfers[key]=dict(vehicle=v.id,remaining=list(ids),elapsed_ms=0)
        w.emit('EMBARK_STARTED',unit=c.unit,vehicle=v.id)
    t=w.transfers[key];v.task_state='WAITING_PASSENGERS'
    ready=True
    for index,id in enumerate(t['remaining']):
        s=w.soldiers[id]
        if hypot(s.pos.x_cm-v.pos.x_cm,s.pos.y_cm-v.pos.y_cm)>200:
            target=(v.pos.x_cm-100+(index%3)*100,v.pos.y_cm-100+(index//3)*100)
            move(w,key+f':approach:{id}',s,target,w.unit_specs[s.type_id]['speed_mps'],ids)
            ready=False
    if not ready:return False
    t['elapsed_ms']+=200
    while t['remaining'] and t['elapsed_ms']>=500:
        t['elapsed_ms']-=500
        id=t['remaining'].pop(0);s=w.soldiers[id]
        v.passenger_ids.append(id);s.carrier_id=v.id;s.task_state='ONBOARD';s.pos=v.pos
        w.emit('EMBARK_DONE',unit=id,vehicle=v.id)
    if not t['remaining']:
        v.task_state='READY'
        return True
    return False


def release_transfer_locks(w):
    for v in w.vehicles.values():
        if v.task_state=='UNLOADING' and not any(t['ids'] and w.queue.commands[k].unit==v.id and w.queue.status.get(k) in ('QUEUED','RUNNING') for k,t in getattr(w,'unloads',{}).items()):
            v.task_state='READY'
        if v.task_state=='WAITING_PASSENGERS' and not any(t['vehicle']==v.id and t['remaining'] and w.queue.status.get(k) in ('QUEUED','RUNNING') for k,t in getattr(w,'transfers',{}).items()):
            v.task_state='READY'


def fly(w,key,v,destination):
    if not hasattr(w,'flights'):w.flights={}
    spec=w.vehicle_specs['HEL']
    landing=FootprintTerrain(w.terrain,[1000,1000])
    def clear_landing(point):
        return landing.passable(*point) and not any(o.id!=v.id and abs(o.pos.x_cm-point[0])<(w.vehicle_specs[o.type_id]['footprint_cm'][0]+800)/2 and abs(o.pos.y_cm-point[1])<(w.vehicle_specs[o.type_id]['footprint_cm'][1]+800)/2 for o in w.vehicles.values())
    if key not in w.flights:
        if not clear_landing(destination) or not clear_landing((v.pos.x_cm,v.pos.y_cm)):
            raise OrderError('LANDING_INVALID')
        if v.task_state in ('WAITING_PASSENGERS','UNLOADING'):
            raise OrderError('ILLEGAL_STATE')
        w.flights[key]=dict(stage='TAKEOFF',elapsed=0,x=float(v.pos.x_cm),y=float(v.pos.y_cm))
    f=w.flights[key];v.task_state=f['stage']
    if f['stage'] in ('TAKEOFF','LANDING'):
        f['elapsed']+=200
        if f['elapsed']>=4000:
            if f['stage']=='LANDING':
                if not clear_landing((v.pos.x_cm,v.pos.y_cm)):raise OrderError('LANDING_INVALID')
                v.task_state='ARRIVED';w.emit('UNIT_ARRIVED',unit=v.id)
                return True
            f['stage']='MOVING';f['elapsed']=0
        return False
    if v.fuel<=0:
        w.emit('VEHICLE_OUT_OF_FUEL',unit=v.id);raise OrderError('NO_FUEL')
    x,y=f['x'],f['y'];tx,ty=destination
    distance=hypot(tx-x,ty-y)
    amount=min(distance,spec['speed_mps']*20,v.fuel/spec['fuel_per_100m']*10000)
    nx,ny=(tx,ty) if amount>=distance else (x+(tx-x)*amount/distance,y+(ty-y)*amount/distance)
    samples=max(1,ceil(amount/50))
    crosses_no_fly=any([round(x+(nx-x)*i/samples)//400,round(y+(ny-y)*i/samples)//400] in getattr(w.terrain,'no_fly',[]) for i in range(samples+1))
    if not w.terrain.inside(round(nx),round(ny)) or crosses_no_fly:
        raise OrderError('NO_FLY')
    v.pos=WorldPos(round(nx),round(ny));f['x'],f['y']=nx,ny
    v.fuel=max(0,v.fuel-amount/10000*spec['fuel_per_100m'])
    for id in v.passenger_ids:w.soldiers[id].pos=v.pos
    w.emit('UNIT_MOVED',unit=v.id,x_cm=v.pos.x_cm,y_cm=v.pos.y_cm)
    if amount>=distance:f['stage']='LANDING';f['elapsed']=0
    return False


def unload(w,key,c):
    v=w.vehicles.get(c.unit)
    if v is None or v.task_state in ('MOVING','TAKEOFF','LANDING','WAITING_PASSENGERS'):
        raise OrderError('ILLEGAL_STATE')
    if hypot(v.pos.x_cm-c.arg0*100,v.pos.y_cm-c.arg1*100)>400:
        raise OrderError('INVALID_TARGET')
    if not hasattr(w,'unloads'):w.unloads={}
    if key not in w.unloads:
        candidates=[]
        for dx in range(-800,801,100):
            for dy in range(-800,801,100):
                if hypot(dx,dy)<=800:
                    candidates.append((dx,dy))
        candidates.sort(key=lambda p:(hypot(*p),p))
        placements=[]
        for dx,dy in candidates:
            x,y=v.pos.x_cm+dx,v.pos.y_cm+dy
            if not w.terrain.passable(x,y):continue
            if any(abs(x-o.pos.x_cm)<w.vehicle_specs[o.type_id]['footprint_cm'][0]/2+50 and abs(y-o.pos.y_cm)<w.vehicle_specs[o.type_id]['footprint_cm'][1]/2+50 for o in w.vehicles.values()):continue
            if any(s.alive and s.carrier_id is None and hypot(s.pos.x_cm-x,s.pos.y_cm-y)<100 for s in w.soldiers.values()):continue
            placements.append((x,y))
            if len(placements)>=len(v.passenger_ids):break
        if len(placements)<len(v.passenger_ids):raise OrderError('NO_DISEMBARK_SPACE')
        w.unloads[key]=dict(ids=list(v.passenger_ids),positions=placements,elapsed=0)
    t=w.unloads[key];v.task_state='UNLOADING';t['elapsed']+=200
    while t['ids'] and t['elapsed']>=500:
        x,y=t['positions'][0]
        if not w.terrain.passable(x,y) or any(s.alive and s.carrier_id is None and hypot(s.pos.x_cm-x,s.pos.y_cm-y)<84 for s in w.soldiers.values()):
            raise OrderError('NO_DISEMBARK_SPACE')
        t['elapsed']-=500;id=t['ids'].pop(0);t['positions'].pop(0)
        s=w.soldiers[id];s.pos=WorldPos(x,y);s.carrier_id=None;s.task_state='IDLE'
        v.passenger_ids.remove(id);w.emit('DISEMBARK_DONE',unit=id,vehicle=v.id,x_cm=x,y_cm=y)
    if not t['ids']:
        v.task_state='IDLE';return True
    return False
