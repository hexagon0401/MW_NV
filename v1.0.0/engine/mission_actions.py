"""Physical objective interactions, using normal paths and actor ownership."""
from dataclasses import replace
from math import hypot
from .types import Op
from .orders import OrderError
from .mission_rules import inside


def enter(w,c):
    if getattr(w,'mode',None)!='capture_flag' or c.unit in w.vehicles:raise OrderError('ILLEGAL_STATE')
    facility=w.facilities.get(c.target)
    if facility is None or facility.kind!='HQ':raise OrderError('INVALID_TARGET')
    return replace(c,op=Op.MOVE,arg0=facility.pos.x_cm//100,arg1=facility.pos.y_cm//100)


def interact(w,key,c):
    if getattr(w,'mode',None)!='capture_flag' or c.unit in w.vehicles:raise OrderError('ILLEGAL_STATE')
    facility=w.facilities.get(c.target)
    if facility is None or facility.kind!='HQ':raise OrderError('INVALID_TARGET')
    flag=w.flags[int(facility.owner)];ids=w.squads[c.unit].member_ids if c.unit in w.squads else [c.unit]
    people=[w.soldiers[i] for i in ids if i in w.soldiers and w.soldiers[i].alive and w.soldiers[i].carrier_id is None]
    if not people:raise OrderError('ILLEGAL_STATE')
    if not hasattr(w,'mission_interactions'):w.mission_interactions={}
    prior=w.mission_interactions.get(key)
    if prior and (flag['status']!=prior['status'] or getattr(w,'ended',False)):return True
    if flag['status']=='home':near=any(inside(s.pos,w.bases[int(facility.owner)]['room']) for s in people)
    elif flag['status']=='dropped':near=any(hypot(s.pos.x_cm-flag['x_cm'],s.pos.y_cm-flag['y_cm'])<=400 for s in people)
    else:near=any(s.id==flag['carrier'] and inside(s.pos,w.bases[int(c.team)]['return_zone']) for s in people)
    if not near:raise OrderError('OUT_OF_RANGE')
    w.mission_interactions[key]=dict(owner=int(facility.owner),status=flag['status'],team=int(c.team))
    for s in people:s.task_state='INTERACTING'
    return False


def speed(w,unit,base):
    if any(f['status']=='carried' and f['carrier']==unit.id for f in getattr(w,'flags',{}).values()):return base*w.scenario['carrier_speed_factor']
    return base
