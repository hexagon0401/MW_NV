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
    if not observer.alive or not target.alive or observer.carrier_id is not None or target.carrier_id is not None:
        return False
    radius=w.unit_specs[observer.type_id]['detection_m']*100
    if w.terrain.tile(observer.pos.x_cm,observer.pos.y_cm)==Tile.FOREST:
        radius*=.7
    if w.terrain.tile(target.pos.x_cm,target.pos.y_cm)==Tile.FOREST:
        radius*=.8
    return hypot(observer.pos.x_cm-target.pos.x_cm,observer.pos.y_cm-target.pos.y_cm)<=radius and line_of_sight(w.terrain,observer.pos,target.pos)


def update_sensing(w):
    if not hasattr(w,'visible'):
        w.visible={t:[] for t in Team};w.last_seen={t:{} for t in Team}
    for team in Team:
        friends=[s for s in w.soldiers.values() if s.team==team]
        visible=[]
        for enemy in sorted(w.soldiers.values(),key=lambda s:s.id):
            if enemy.team!=team and any(can_see(w,s,enemy) for s in friends):
                visible.append(enemy.id)
                w.last_seen[team][str(enemy.id)]=dict(id=enemy.id,x_cm=enemy.pos.x_cm,y_cm=enemy.pos.y_cm,seen_at_tick=w.tick)
                if enemy.id not in w.visible[team]:
                    w.emit('UNIT_SPOTTED',team=int(team),unit=enemy.id)
        w.visible[team]=visible
        w.last_seen[team]={k:v for k,v in w.last_seen[team].items() if w.tick-v['seen_at_tick']<300}


def observation(w,team):
    team=Team(team)
    visible=getattr(w,'visible',{}).get(team,[])
    return deepcopy(dict(team=int(team),color='blue' if team==Team.A else 'red',tick=w.tick,
        units=[s.to_dict() for s in sorted(w.soldiers.values(),key=lambda s:s.id) if s.team==team],
        squads=[s.to_dict() for s in w.squads.values() if s.team==team],
        vehicles=[s.to_dict() for s in w.vehicles.values() if s.team==team],
        enemies=[w.soldiers[i].to_dict() for i in visible if w.soldiers[i].alive],
        last_seen=list(getattr(w,'last_seen',{}).get(team,{}).values()),
        facilities=[asdict(f) for f in w.facilities.values()],
        orders=[dict(cmd_id=c.cmd_id,status=w.queue.status[k]) for k,c in w.queue.commands.items() if c.team==team][-10:] if hasattr(w,'queue') else [],
        resources=asdict(w.teams[team]),scores={int(t):s.score for t,s in w.teams.items()}))
