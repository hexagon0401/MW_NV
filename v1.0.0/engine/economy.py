"""Atomic purchase of individual arcade units at an owned HQ."""
from math import hypot
from .types import Team,WorldPos,Vehicle,Squad
from .catalog import make_soldier
from .logistics import debit
from .orders import OrderError
from .transport import FootprintTerrain

PURCHASE_TYPES=('INF','REC','SUP','MED','ENG','LUV','APC','IFV','HEL','TRK','AT','MBT','SPH')


def purchase(w,c):
    if not 0<=c.arg0<len(PURCHASE_TYPES):raise OrderError('INVALID_TARGET')
    hq=w.facilities.get(c.target)
    if hq is None or hq.kind!='HQ' or hq.owner!=c.team:raise OrderError('FOREIGN_UNIT')
    kind=PURCHASE_TYPES[c.arg0];infantry=kind in w.unit_specs
    collection=w.soldiers if infantry else w.vehicles
    active=sum(u.team==c.team and getattr(u,'alive',True) for u in collection.values())
    if active>=(96 if infantry else 14):raise OrderError('NO_CAPACITY')
    spec=(w.unit_specs if infantry else w.vehicle_specs)[kind]
    terrain=w.terrain if infantry else FootprintTerrain(w.terrain,spec['footprint_cm'])
    position=None
    for radius in range(0,2001,100):
        for dx,dy in ((radius,0),(-radius,0),(0,radius),(0,-radius)):
            x,y=hq.pos.x_cm+dx,hq.pos.y_cm+dy
            if not terrain.passable(x,y):continue
            if any(s.alive and s.carrier_id is None and hypot(s.pos.x_cm-x,s.pos.y_cm-y)<100 for s in w.soldiers.values()):continue
            if any(abs(v.pos.x_cm-x)<(w.vehicle_specs[v.type_id]['footprint_cm'][0]+(100 if infantry else spec['footprint_cm'][0]))/2 and abs(v.pos.y_cm-y)<(w.vehicle_specs[v.type_id]['footprint_cm'][1]+(100 if infantry else spec['footprint_cm'][1]))/2 for v in w.vehicles.values()):continue
            position=WorldPos(x,y);break
        if position:break
    if position is None:raise OrderError('NO_SPAWN_SPACE')
    debit(w,c.team,credits=spec['cost'],tickets=1 if infantry else 0)
    id=max([0,*w.soldiers,*w.vehicles,*w.squads,*w.facilities])+1
    unit=make_soldier(id,c.team,position,kind,w.unit_specs) if infantry else Vehicle(id,c.team,position,kind)
    collection[id]=unit
    if infantry:
        groups=sorted((g for g in w.squads.values() if g.team==c.team and any(w.soldiers[i].type_id==kind for i in g.member_ids)),key=lambda g:g.id)
        destination=next((g for g in groups if sum(w.soldiers[i].alive for i in g.member_ids)<8),None)
        if destination is None:
            gid=id+1;destination=Squad(gid,c.team,position,[id]);w.squads[gid]=destination
        else:
            destination.member_ids=[i for i in destination.member_ids if w.soldiers[i].alive]+[id]
        unit.squad_id=destination.id
    w.emit('UNIT_SPAWNED' ,unit=id,entity=dict(id=id,team=int(c.team),type_id=kind,x_cm=position.x_cm,y_cm=position.y_cm,size_px=spec['size_px'],alive=True,carrier_id=None))
