"""Detached spectator frames and completed-match exports."""
import json
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from .replay import RecordingEngine
from .scenario import create_release_match
from .types import Team,WorldPos
from .objectives import summary


def frame(w):
    """Detached presentation snapshot. Reading it cannot alter world/checksum."""
    units=[];attacks={};shots=[];impacts=[];damage=[]
    for event in reversed(w.events):
        if event['sim_tick']<w.tick-10:break
        if event['event_kind'] in ('ARTILLERY_IMPACT','TANK_IMPACT'):impacts.append(dict(event['payload'],tick=event['sim_tick']))
        if event['event_kind']=='UNIT_DAMAGED' and event['payload']['damage']:damage.append(dict(event['payload'],tick=event['sim_tick']))
        if event['event_kind']=='ABSTRACT_ATTACK':
            attacks.setdefault(event['payload']['unit'],event['sim_tick']+11)
            shots.append(dict(event['payload'],tick=event['sim_tick']))
    for collection in (w.soldiers,w.vehicles):
        for u in collection.values():
            soldier=u.id in w.soldiers
            spec=(w.unit_specs if soldier else w.vehicle_specs)[u.type_id]
            units.append(dict(id=u.id,team=int(u.team),type_id=u.type_id,x_cm=u.pos.x_cm,y_cm=u.pos.y_cm,
                size_px=list(spec['size_px']),alive=getattr(u,'alive',True),carrier_id=getattr(u,'carrier_id',None),
                task_state=u.task_state,activity='FIRING' if u.id in attacks and getattr(u,'alive',True) and getattr(u,'carrier_id',None) is None else None,activity_until_tick=attacks.get(u.id),squad_id=getattr(u,'squad_id',None),hp=getattr(u,'hp',None),
                armor=spec['armor'],weapon=spec['weapon'],role=spec['role'],cooldown_ms=u.cooldown_ms,deployment=getattr(u,'deployment',None),deployment_ms=getattr(u,'deployment_ms',None),turret_heading=getattr(u,'turret_heading',None),max_ammo=spec['ammo'],min_range_m=100 if u.type_id=='SPH' else 0,passenger_count=len(getattr(u,'passenger_ids',[])),max_hp=spec.get('hp'),target_id=getattr(u,'target_id',None),range_m=(spec.get('attack') or {}).get('range_m'),ammo=getattr(u,'ammo',None),fuel=getattr(u,'fuel',None)))
    decisions={}
    for event in reversed(w.events):
        if event['event_kind']=='HQ_DECISION':
            team=str(event['payload']['team'])
            if team not in decisions:decisions[team]=deepcopy(event['payload']['metadata'])
            if len(decisions)==2:break
    orders=[]
    if hasattr(w,'queue'):
        for team in Team:
            commands=[c for c in w.queue.commands.values() if c.team==team][-10:]
            for c in commands:
                orders.append(dict(team=int(team),cmd_id=c.cmd_id,op=int(c.op),unit=c.unit,arg0=c.arg0,arg1=c.arg1,
                    target=c.target,accepted_tick=c.tick,status=w.queue.status[f'{int(team)}:{c.cmd_id}']))
    return dict(presentation_version=3,decisions=decisions,rules_version=w.rules_version,projectiles=deepcopy(w.projectiles),impacts=impacts,damage=damage,shots=shots,tick=w.tick,units=units,squads=[asdict(s) for s in w.squads.values()],orders=orders,
        scores={int(t):s.score for t,s in w.teams.items()},facilities=[dict(id=f.id,kind=f.kind,
        x_cm=f.pos.x_cm,y_cm=f.pos.y_cm,owner=None if f.owner is None else int(f.owner),
        radius_cm=f.radius_cm,capturing=None if f.capturing is None else int(f.capturing),progress_ms=f.progress_ms)
        for f in w.facilities.values()])


def export_view(engine,initial):
    w=engine.world
    if not getattr(w,'ended',False):raise ValueError('only completed matches may be published')
    ordered=[(e['sim_tick'],i,deepcopy(e)) for i,e in enumerate(w.events)]
    ordered.extend((e['sim_tick'],e['after_event_count']-.5,{k:deepcopy(v) for k,v in e.items() if k!='after_event_count'}) for e in getattr(engine,'presentation_events',[]))
    events=[e for _,_,e in sorted(ordered,key=lambda row:(row[0],row[1]))]
    for i,event in enumerate(events):event['event_id']=i
    for event in events:
        p=event['payload']
        if event['event_kind']=='ORDER_ACCEPTED' and hasattr(w,'queue'):
            c=w.queue.commands.get(f"{p['team']}:{p['cmd_id']}")
            if c is not None:p.update(op=int(c.op),unit=c.unit,arg0=c.arg0,arg1=c.arg1,target=c.target)
    initial=deepcopy(initial)
    return dict(version=1,presentation_version=4,map_id=getattr(w,'map_id',None),map_version=getattr(w,'map_version',None),rules_version=w.rules_version,catalog=dict(version=w.catalog_version,units=deepcopy(w.unit_specs),vehicles=deepcopy(w.vehicle_specs),weapons=deepcopy(w.weapon_specs)),width_m=w.config.map_width_m,height_m=w.config.map_height_m,
        terrain=deepcopy(w.terrain.cells),units=initial['units'],initial=initial,final=frame(w),events=events,summary=summary(w))


def demo(output):
    w=create_release_match(1)
    group=w.squads[10100]
    for i,id in enumerate(group.member_ids):w.soldiers[id].pos=WorldPos(49000-(i//2)*150,22400+(i%2)*150)
    group.pos=w.soldiers[group.member_ids[0]].pos
    e=RecordingEngine(w);initial=frame(e.world)
    e.submit(dict(cmd_id=1,team=0,op=2,unit=10100,arg0=512,arg1=224,ttl=3000))
    e.step(3000)
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(export_view(e,initial),separators=(',',':')))
    Path('data').mkdir(exist_ok=True)
    Path('data/demo.replay.json').write_text(json.dumps(e.document(),separators=(',',':')))
    return e


if __name__=='__main__':demo('viewer/public/demo.json')
