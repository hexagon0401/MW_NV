"""Finite attrition and physical flag missions; ties resolved after both teams."""
from math import hypot
from .types import Team
from .scenario_spec import rules
from .mode_rules import end
from .capabilities import enabled


def combat_possible(w,team):
    if any(u.alive and u.team==team and (w.unit_specs if u.id in w.soldiers else w.vehicle_specs)[u.type_id]['attack'] and enabled(w,u) for u in [*w.soldiers.values(),*w.vehicles.values()]):return True
    state=w.teams[team];spec=rules(w)
    for catalog,cap in ((w.unit_specs,spec['infantry_limit']),(w.vehicle_specs,spec['vehicle_limit'])):
        infantry=catalog is w.unit_specs;living=sum(u.alive and u.team==team and u.type_id!='AA_SITE' for u in (w.soldiers.values() if infantry else w.vehicles.values()))
        if living>=cap:continue
        if any(s['attack'] and not s.get('immobile') and s['cost']<=state.credits and (not infantry or state.tickets>0) for s in catalog.values()):return True
    return any(u.alive and u.team==team and u.carrier_id is None for u in w.soldiers.values()) and any(v.alive and v.type_id=='AA_SITE' and v.team is None and v.ammo>0 for v in w.vehicles.values())


def inside(pos,rect):return rect[0]<=pos.x_cm<rect[2] and rect[1]<=pos.y_cm<rect[3]

def eligible(w,team,rect):return sorted((s for s in w.soldiers.values() if s.alive and s.team==team and s.carrier_id is None and inside(s.pos,rect)),key=lambda s:s.id)

def reset_flag(w,flag,reason):
    flag.update(status='home',carrier=None,x_cm=flag['home'][0],y_cm=flag['home'][1],progress_ms=0,dropped_tick=None,interaction_ms=0)
    w.emit('FLAG_RETURNED',owner=flag['owner'],reason=reason)


def flags_update(w):
    telemetry(w)
    config=rules(w);scored=[];home_at_start={owner:flag['status']=='home' for owner,flag in w.flags.items()}
    for owner in (0,1):
        flag=w.flags[owner];enemy=1-owner;home=w.bases[owner]
        if flag['status']=='carried':
            carrier=w.soldiers.get(flag['carrier'])
            if carrier is None or not carrier.alive:
                if carrier:flag['x_cm']=carrier.pos.x_cm;flag['y_cm']=carrier.pos.y_cm
                flag.update(status='dropped',carrier=None,dropped_tick=w.tick,interaction_ms=0,return_ms=0)
                w.emit('FLAG_DROPPED',owner=owner,x_cm=flag['x_cm'],y_cm=flag['y_cm'])
            else:
                flag.update(x_cm=carrier.pos.x_cm,y_cm=carrier.pos.y_cm)
                own_flag=w.flags[enemy]
                returned=carrier.carrier_id is None and inside(carrier.pos,w.bases[enemy]['return_zone']) and home_at_start[enemy]
                flag['return_ms']=flag.get('return_ms',0)+200 if returned else 0
                if flag['return_ms']>=config['return_seconds']*1000:scored.append(Team(enemy))
        elif flag['status']=='dropped':
            if (w.tick-flag['dropped_tick'])*.2>=config['auto_return_seconds']:reset_flag(w,flag,'timeout');continue
            near={t:sorted((s for s in w.soldiers.values() if s.alive and s.team==t and s.carrier_id is None and hypot(s.pos.x_cm-flag['x_cm'],s.pos.y_cm-flag['y_cm'])<=400),key=lambda s:s.id) for t in (0,1)}
            if near[0] and near[1]:continue
            actor=next((t for t in (0,1) if near[t]),None)
            if actor is None:flag['interaction_ms']=0;continue
            if flag.get('interaction_team')!=actor:flag['interaction_ms']=0
            flag['interaction_team']=actor;flag['interaction_ms']+=200
            if flag['interaction_ms']>=config['recover_seconds' if actor==owner else 'pickup_seconds']*1000:
                if actor==owner:reset_flag(w,flag,'recovered')
                else:
                    flag.update(status='carried',carrier=near[actor][0].id,return_ms=0,interaction_ms=0)
                    w.emit('FLAG_PICKED_UP',owner=owner,team=actor,carrier=flag['carrier'])
        else:
            attackers=eligible(w,enemy,home['room']);defenders=eligible(w,owner,home['room'])
            if not attackers:flag['progress_ms']=0
            elif len(attackers)>=config['steal_troops'] and not defenders:
                flag['progress_ms']+=200
                if flag['progress_ms']>=config['steal_seconds']*1000:
                    flag.update(status='carried',carrier=attackers[0].id,return_ms=0)
                    w.emit('FLAG_STOLEN',owner=owner,team=enemy,carrier=flag['carrier'],participants=[u.id for u in attackers])
    for key,request in getattr(w,'mission_interactions',{}).items():
        flag=w.flags[request['owner']]
        if w.queue.status.get(key)=='RUNNING' and (flag['status']!=request['status'] or request['team'] in scored):w.queue.finish(w,key)
    if scored:
        winners=set(scored)
        for team in winners:w.teams[team].score+=1
        end(w,next(iter(winners)) if len(winners)==1 else None,'FLAG_RETURN' if len(winners)==1 else 'SIMULTANEOUS_FLAG_RETURN')


def update(w):
    config=rules(w)
    if config['mode']=='elimination':
        alive={t:combat_possible(w,t) for t in Team}
        if not all(alive.values()):
            winner=next((t for t in Team if alive[t]),None);end(w,winner,'COMBAT_EXHAUSTED' if winner is not None else 'SIMULTANEOUS_EXHAUSTION');return
    elif config['mode']=='capture_flag':flags_update(w)
    if not getattr(w,'ended',False) and (w.tick+1)*.2>=config['time_limit_s']:end(w,None,'TIME_LIMIT_DRAW')


def telemetry(w):
    if not hasattr(w,'mission_room_presence'):w.mission_room_presence={}
    for owner,base in w.bases.items():
        people=eligible(w,1-owner,base['room']);present={u.id for u in people};old=set(w.mission_room_presence.get(owner,[]))
        for u in people:
            if u.id not in old:
                door=min(range(len(base['doors'])),key=lambda i:hypot(u.pos.x_cm-base['doors'][i][0],u.pos.y_cm-base['doors'][i][1]));w.emit('BUILDING_ENTERED',unit=u.id,team=int(u.team),owner=owner,door=door,x_cm=u.pos.x_cm,y_cm=u.pos.y_cm)
        w.mission_room_presence[owner]=sorted(present)
    if w.tick%5:return
    if not hasattr(w,'flag_tracks'):w.flag_tracks={}
    for owner,flag in w.flags.items():
        carrier=w.soldiers.get(flag['carrier']) if flag['carrier'] is not None else None
        if flag['status']!='carried' or carrier is None or not carrier.alive:w.flag_tracks.pop(owner,None);continue
        prior=w.flag_tracks.get(owner);distance=round(hypot(carrier.pos.x_cm-prior[1],carrier.pos.y_cm-prior[2])) if prior and prior[0]==carrier.id else 0
        w.flag_tracks[owner]=(carrier.id,carrier.pos.x_cm,carrier.pos.y_cm)
        if distance:w.emit('FLAG_MOVED',owner=owner,carrier=carrier.id,team=int(carrier.team),x_cm=carrier.pos.x_cm,y_cm=carrier.pos.y_cm,distance_cm=distance,transport=carrier.carrier_id)
