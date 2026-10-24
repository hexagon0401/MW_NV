"""Seeded arcade damage events; no vehicle attacks or ballistics."""
from math import hypot
from .sensing import can_see
from .map import Tile


def engagement_target(w, s):
    attack=w.unit_specs[s.type_id]['attack']
    if not s.alive or s.carrier_id is not None or not attack or s.ammo<=0:return None
    candidates=[t for t in w.soldiers.values() if t.team!=s.team and can_see(w,s,t)
                and hypot(t.pos.x_cm-s.pos.x_cm,t.pos.y_cm-s.pos.y_cm)<=attack['range_m']*100]
    return min(candidates,key=lambda t:(hypot(t.pos.x_cm-s.pos.x_cm,t.pos.y_cm-s.pos.y_cm),t.id),default=None)


def update_combat(w):
    for s in sorted(w.soldiers.values(),key=lambda s:s.id):
        s.cooldown_ms=max(0,s.cooldown_ms-200)
        attack=w.unit_specs[s.type_id]['attack']
        if s.cooldown_ms:continue
        target=engagement_target(w,s)
        s.target_id=None if target is None else target.id
        if target is None:continue
        chance=attack['hit_probability']*(.8 if w.terrain.tile(target.pos.x_cm,target.pos.y_cm)==Tile.FOREST else 1)
        hit=w.rng.random()<chance
        s.ammo-=1;s.cooldown_ms=attack['interval_ms']
        damage=min(target.hp,attack['damage']) if hit else 0
        target.hp-=damage
        w.emit('ABSTRACT_ATTACK',unit=s.id,target=target.id,damage=damage,hit=hit,range_m=attack['range_m'],distance_m=round(hypot(target.pos.x_cm-s.pos.x_cm,target.pos.y_cm-s.pos.y_cm)/100,2),hit_probability=chance,target_hp=target.hp)
        if target.hp==0:
            target.alive=False;target.task_state='DISABLED'
            w.emit('INFANTRY_DISABLED',unit=target.id)
