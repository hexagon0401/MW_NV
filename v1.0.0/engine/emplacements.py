"""Crewed neutral weapons; no free repair or ammunition on ownership changes."""
from math import hypot
from .orders import OrderError
from .types import Team

def operate(w,key,command,leave=False):
    soldier=w.soldiers.get(command.unit);station=w.vehicles.get(command.target)
    if soldier is None or not soldier.alive or station is None or station.type_id!='AA_SITE' or not station.alive:raise OrderError('INVALID_TARGET')
    if leave:
        if station.crew_id!=soldier.id or soldier.team!=command.team:raise OrderError('FOREIGN_UNIT')
        soldier.carrier_id=None;soldier.task_state='IDLE';station.crew_id=None;station.team=None;station.passenger_ids=[]
        w.emit('DISEMBARK_DONE',unit=soldier.id,vehicle=station.id,x_cm=soldier.pos.x_cm,y_cm=soldier.pos.y_cm)
        w.emit('EMPLACEMENT_LEFT',unit=soldier.id,vehicle=station.id);return True
    if soldier.carrier_id is not None:raise OrderError('ILLEGAL_STATE')
    if hypot(soldier.pos.x_cm-station.pos.x_cm,soldier.pos.y_cm-station.pos.y_cm)>400:raise OrderError('OUT_OF_RANGE')
    if station.crew_id is not None:raise OrderError('OCCUPIED')
    if any(u.alive and u.team!=command.team and u.carrier_id is None and hypot(u.pos.x_cm-station.pos.x_cm,u.pos.y_cm-station.pos.y_cm)<=800 for u in w.soldiers.values()):return False
    if not hasattr(w,'emplacement_timers'):w.emplacement_timers={}
    w.emplacement_timers[key]=w.emplacement_timers.get(key,0)+200;soldier.task_state='OPERATING'
    if w.emplacement_timers[key]<8000:return False
    station.team=command.team;station.crew_id=soldier.id;soldier.carrier_id=station.id;soldier.task_state='ONBOARD';station.passenger_ids=[soldier.id]
    w.emit('EMPLACEMENT_CAPTURED',unit=station.id,team=int(command.team),crew=soldier.id);return True

def update(w):
    for station in w.vehicles.values():
        if station.type_id!='AA_SITE' or station.crew_id is None:continue
        soldier=w.soldiers.get(station.crew_id)
        if not station.alive or soldier is None or not soldier.alive or soldier.carrier_id!=station.id:
            station.crew_id=None;station.team=None;station.passenger_ids=[];station.passenger_ids=[];station.target_id=None
            w.emit('EMPLACEMENT_INACTIVE',unit=station.id)
