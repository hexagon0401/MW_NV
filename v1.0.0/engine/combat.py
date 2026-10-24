"""Seeded arcade damage events; no vehicle attacks or ballistics."""
from math import hypot
from .sensing import can_see
from .map import Tile


def update_combat(w):
    for s in sorted(w.soldiers.values(),key=lambda s:s.id):
        s.cooldown_ms=max(0,s.cooldown_ms-200)
        attack=w.unit_specs[s.type_id]['attack']
        if not s.alive or s.carrier_id is not None or not attack or s.ammo<=0 or s.cooldown_ms or s.task_state not in ('IDLE','HOLD','DEFEND','ARRIVED','BLOCKED'):
            continue
        candidates=[t for t in w.soldiers.values() if t.team!=s.team and t.id in getattr(w,'visible',{}).get(s.team,[]) and can_see(w,s,t) and hypot(t.pos.x_cm-s.pos.x_cm,t.pos.y_cm-s.pos.y_cm)<=attack['range_m']*100]
        if not candidates:
            continue
        target=min(candidates,key=lambda t:(hypot(t.pos.x_cm-s.pos.x_cm,t.pos.y_cm-s.pos.y_cm),t.id))
        chance=attack['hit_probability']*(.8 if w.terrain.tile(target.pos.x_cm,target.pos.y_cm)==Tile.FOREST else 1)
        hit=w.rng.random()<chance
        s.ammo-=1;s.cooldown_ms=attack['interval_ms']
        damage=min(target.hp,attack['damage']) if hit else 0
        target.hp-=damage
        w.emit('ABSTRACT_ATTACK',unit=s.id,target=target.id,damage=damage)
        if target.hp==0:
            target.alive=False;target.task_state='DISABLED'
            w.emit('INFANTRY_DISABLED',unit=target.id)
