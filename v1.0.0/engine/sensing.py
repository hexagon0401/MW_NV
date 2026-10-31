"""Team-owned visibility snapshots; observations contain no live references."""
from copy import deepcopy
from math import hypot,ceil
from dataclasses import asdict
from .types import Team
from .map import Tile


def line_of_sight(terrain,a,b):
    n=max(1,ceil(hypot(b.x_cm-a.x_cm,b.y_cm-a.y_cm)/100))
    return all(terrain.tile(round(a.x_cm+(b.x_cm-a.x_cm)*i/n),round(a.y_cm+(b.y_cm-a.y_cm)*i/n)) not in (Tile.WALL,Tile.BUILDING_INTERIOR) for i in range(n+1))


def can_see(w,observer,target):
    if not observer.alive or not target.alive or getattr(observer,'carrier_id',None) is not None or getattr(target,'carrier_id',None) is not None:
        return False
    radius=(w.unit_specs if observer.id in w.soldiers else w.vehicle_specs)[observer.type_id]['detection_m']*100
    if any((f.kind=='TOWER' or f.id==201 and f.kind=='OBJECTIVE') and f.owner==observer.team and hypot(f.pos.x_cm-observer.pos.x_cm,f.pos.y_cm-observer.pos.y_cm)<=f.radius_cm for f in w.facilities.values()):
        radius*=1.2
    if w.terrain.tile(observer.pos.x_cm,observer.pos.y_cm)==Tile.FOREST:
        radius*=.7
    if w.terrain.tile(target.pos.x_cm,target.pos.y_cm)==Tile.FOREST:
        radius*=.8
    return hypot(observer.pos.x_cm-target.pos.x_cm,observer.pos.y_cm-target.pos.y_cm)<=radius and line_of_sight(w.terrain,observer.pos,target.pos)


def update_sensing(w):
    if not hasattr(w,'visible'):
        w.visible={t:[] for t in Team};w.last_seen={t:{} for t in Team}
    buckets={}
    for s in [*w.soldiers.values(),*w.vehicles.values()]:
        if s.alive and getattr(s,'carrier_id',None) is None:buckets.setdefault((s.pos.x_cm//800,s.pos.y_cm//800),[]).append(s)
    for team in Team:
        found=set()
        for observer in [*w.soldiers.values(),*w.vehicles.values()]:
            if observer.team!=team or not observer.alive or getattr(observer,'carrier_id',None) is not None:continue
            radius=ceil((w.unit_specs if observer.id in w.soldiers else w.vehicle_specs)[observer.type_id]['detection_m']*1.2/8)
            cx,cy=observer.pos.x_cm//800,observer.pos.y_cm//800
            for x in range(cx-radius,cx+radius+1):
                for y in range(cy-radius,cy+radius+1):
                    for enemy in buckets.get((x,y),()):
                        if enemy.team!=team and enemy.id not in found and can_see(w,observer,enemy):found.add(enemy.id)
        visible=sorted(found)
        for id in visible:
            enemy=w.soldiers.get(id) or w.vehicles[id]
            w.last_seen[team][str(id)]=dict(id=id,x_cm=enemy.pos.x_cm,y_cm=enemy.pos.y_cm,seen_at_tick=w.tick)
            if id not in w.visible[team]:w.emit('UNIT_SPOTTED',team=int(team),unit=id)
        w.visible[team]=visible
        w.last_seen[team]={k:v for k,v in w.last_seen[team].items() if w.tick-v['seen_at_tick']<300}


def observation(w,team):
    team=Team(team);orders=[]
    if hasattr(w,'queue'):
        own=[(k,c) for k,c in w.queue.commands.items() if c.team==team]
        recent={k for k,c in own[-10:]}
        orders=[dict(cmd_id=c.cmd_id,status=w.queue.status[k],unit=c.unit,op=int(c.op),target=c.target,arg0=c.arg0,arg1=c.arg1) for k,c in own if k in recent or w.queue.status[k] in ('QUEUED','RUNNING')]
    visible=getattr(w,'visible',{}).get(team,[])
    from .mission_observation import observed
    mission=observed(w,team)
    result=deepcopy(dict(mission=mission,rules_version=w.rules_version,catalog=dict(units=w.unit_specs,vehicles=w.vehicle_specs,weapons=w.weapon_specs),team=int(team),map_width_m=w.config.map_width_m,map_height_m=w.config.map_height_m,color='blue' if team==Team.A else 'red',tick=w.tick,
        units=[s.to_dict() for s in sorted(w.soldiers.values(),key=lambda s:s.id) if s.team==team],
        squads=[s.to_dict() for s in w.squads.values() if s.team==team],
        vehicles=[v.to_dict() for v in w.vehicles.values() if v.team==team],
        enemies=[u.to_dict() for uid in visible if (u:=w.soldiers.get(uid) or w.vehicles.get(uid)) is not None and u.alive and u.team is not None],
        failed_goals=[g for g in getattr(w,'failed_goals',[]) if g['team']==int(team) and g['until_tick']>w.tick and g['terrain_revision']==w.terrain.revision],last_seen=list(getattr(w,'last_seen',{}).get(team,{}).values()),facilities=[asdict(f) for f in w.facilities.values()],orders=orders,
        terrain=None,resources=asdict(w.teams[team]),scores={int(t):v.score for t,v in w.teams.items()}))

    # Cells are integers: copying each row detaches the same public list interface
    # without recursively visiting every scalar on each HQ observation.
    result['terrain']=[row.copy() for row in w.terrain.cells] if w.config.map_width_m>=1024 else None
    return result
