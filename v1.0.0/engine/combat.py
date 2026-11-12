"""Deterministic role-based direct fire and observed-coordinate indirect fire."""
from math import hypot,atan2,cos,sin,pi
from .sensing import can_see
from .map import Tile
from .types import WorldPos
from .orders import OrderError
from .capabilities import aircraft,airborne,attack_allowed


def spec(w,u):
    return (w.unit_specs if u.id in w.soldiers else w.vehicle_specs)[u.type_id]


def entities(w):return [*w.soldiers.values(),*w.vehicles.values()]


def armor(w,u):
    return 'light' if aircraft(w,u) and not airborne(w,u) else spec(w,u)['armor']


def multiplier(w,attacker,target):
    return w.weapon_specs['multipliers'][spec(w,attacker)['weapon']][armor(w,target)]


def engagement_target(w,u):
    attack=spec(w,u)['attack']
    if u.task_state=='RESUPPLYING' or not u.alive or getattr(u,'carrier_id',None) is not None or not attack or u.ammo<=0 or u.type_id=='SPH':return None
    # Sensing is shared by team, but direct fire still requires this actor's LOS/range.
    ids=getattr(w,'visible',{}).get(u.team,[])
    candidates=[]
    for uid in ids:
        t=w.soldiers.get(uid) or w.vehicles.get(uid)
        if t and (t.team is not None or t.type_id=='AA_SITE' and t.id==u.target_id) and t.team!=u.team and attack_allowed(w,u,t) and can_see(w,u,t) and hypot(t.pos.x_cm-u.pos.x_cm,t.pos.y_cm-u.pos.y_cm)<=attack['range_m']*100 and multiplier(w,u,t)>0 and tank_safe(w,u,t):candidates.append(t)
    preferred=next((t for t in candidates if t.id==u.target_id),None)
    return preferred or min(candidates,key=lambda t:(-attack['damage']*multiplier(w,u,t)/max(1,t.hp),hypot(t.pos.x_cm-u.pos.x_cm,t.pos.y_cm-u.pos.y_cm),t.id),default=None)


def tank_safe(w,actor,target):
    if actor.type_id!='MBT':return True
    blast=w.weapon_specs['tank_splash']['blast_m']*100
    return not any(u.team==actor.team and u.alive and getattr(u,'carrier_id',None) is None and armor(w,u)!='air' and hypot(u.pos.x_cm-target.pos.x_cm,u.pos.y_cm-target.pos.y_cm)<blast for u in entities(w))


def blast_plan(w,x,y,radius,damage,exclude=()):
    # Snapshot all eligible targets before any vehicle death can evacuate passengers.
    result=[]
    for u in sorted(entities(w),key=lambda v:v.id):
        if u.id in exclude or not u.alive or getattr(u,'carrier_id',None) is not None or armor(w,u)=='air':continue
        distance=hypot(u.pos.x_cm-x,u.pos.y_cm-y)
        if distance>=radius:continue
        amount=round(damage*(1-distance/radius)*w.weapon_specs['multipliers']['he'][armor(w,u)])
        if amount>0:result.append((u,amount))
    return result


def damage_unit(w,target,amount,source=None,cause=None):
    if not target.alive:return
    damage=min(target.hp,max(0,int(amount)));target.hp-=damage
    attacker=w.soldiers.get(source) or w.vehicles.get(source)
    w.emit('UNIT_DAMAGED',unit=target.id,source=source,damage=damage,hp=target.hp,x_cm=target.pos.x_cm,y_cm=target.pos.y_cm,friendly_fire=attacker is not None and attacker.team==target.team,cause=cause)
    if target.hp>0:return
    target.alive=False;target.task_state='DISABLED';target.target_id=None
    if target.id in w.soldiers:
        w.emit('INFANTRY_DISABLED',unit=target.id);return
    w.emit('VEHICLE_DISABLED',unit=target.id)
    # Deterministic emergency disembark; dead wreck is deliberately nonblocking.
    for uid in list(target.passenger_ids):
        soldier=w.soldiers[uid];soldier.carrier_id=None
        damage_unit(w,soldier,25,source)
        placed=False
        if soldier.alive:
            for radius in range(100,1601,100):
                for dx,dy in ((-radius,0),(radius,0),(0,-radius),(0,radius),(-radius,-radius),(radius,radius),(-radius,radius),(radius,-radius)):
                    x,y=target.pos.x_cm+dx,target.pos.y_cm+dy
                    if not w.terrain.passable(x,y):continue
                    if any(v.alive and abs(v.pos.x_cm-x)<w.vehicle_specs[v.type_id]['footprint_cm'][0]/2+50 and abs(v.pos.y_cm-y)<w.vehicle_specs[v.type_id]['footprint_cm'][1]/2+50 for v in w.vehicles.values()):continue
                    if any(s.id!=uid and s.alive and s.carrier_id is None and hypot(s.pos.x_cm-x,s.pos.y_cm-y)<100 for s in w.soldiers.values()):continue
                    soldier.pos=WorldPos(x,y);soldier.task_state='IDLE';placed=True
                    w.emit('DISEMBARK_DONE',unit=uid,vehicle=target.id,x_cm=x,y_cm=y,emergency=True);break
                if placed:break
            if not placed:damage_unit(w,soldier,soldier.hp,source)
    target.passenger_ids.clear()


def fire_mission(w,key,c):
    u=w.vehicles.get(c.unit);settings=w.weapon_specs['artillery']
    if u is None or u.type_id!='SPH' or not u.alive or u.deployment!='DEPLOYED' or u.task_state=='MOVING':raise OrderError('ILLEGAL_STATE')
    if u.ammo<=0:raise OrderError('NO_AMMO')
    x,y=c.arg0*100,c.arg1*100;distance=hypot(x-u.pos.x_cm,y-u.pos.y_cm)
    if not settings['min_range_m']*100<=distance<=spec(w,u)['attack']['range_m']*100:raise OrderError('OUT_OF_RANGE')
    observations=[dict(x_cm=t.pos.x_cm,y_cm=t.pos.y_cm,seen_at_tick=w.tick) for t in entities(w) if t.id in getattr(w,'visible',{}).get(u.team,[]) and t.team!=u.team and t.alive]
    observations+=list(getattr(w,'last_seen',{}).get(u.team,{}).values())
    if not any(0<=w.tick-o['seen_at_tick']<=settings['observation_ticks'] and hypot(o['x_cm']-x,o['y_cm']-y)<=100 for o in observations):raise OrderError('UNOBSERVED_TARGET')
    if u.cooldown_ms:return False
    angle=w.artillery_rng.random()*2*pi;radius=w.artillery_rng.random()**.5*settings['scatter_m']*100
    ix=max(0,min(w.config.map_width_m*100-1,round(x+cos(angle)*radius)))
    iy=max(0,min(w.config.map_height_m*100-1,round(y+sin(angle)*radius)))
    projectile=dict(unit=u.id,team=int(u.team),fired_tick=w.tick,origin=dict(x_cm=u.pos.x_cm,y_cm=u.pos.y_cm),x_cm=ix,y_cm=iy,impact_tick=w.tick+settings['flight_ticks'],damage=spec(w,u)['attack']['damage'])
    w.projectiles.append(projectile);u.ammo-=1;u.cooldown_ms=spec(w,u)['attack']['interval_ms'];u.turret_heading=atan2(y-u.pos.y_cm,x-u.pos.x_cm)
    w.emit('ARTILLERY_FIRED',**projectile,blast_m=settings['blast_m'],ammo=u.ammo);return True


def deployment(w,u,pack=False):
    if u.type_id!='SPH' or not u.alive:raise OrderError('INVALID_TARGET')
    goal='PACKED' if pack else 'DEPLOYED';stage='PACKING' if pack else 'DEPLOYING'
    if u.deployment==goal:return True
    if u.task_state=='MOVING':raise OrderError('ILLEGAL_STATE')
    if u.deployment!=stage:u.deployment=stage;u.deployment_ms=0
    u.deployment_ms+=200;u.task_state=stage
    limit=w.weapon_specs['artillery']['pack_ms' if pack else 'deploy_ms']
    if u.deployment_ms>=limit:
        u.deployment=goal;u.task_state='IDLE';w.emit('DEPLOYMENT_CHANGED',unit=u.id,deployment=goal);return True
    return False


def update_combat(w):
    for u in sorted(entities(w),key=lambda u:u.id):
        u.cooldown_ms=max(0,u.cooldown_ms-200)
        if not u.alive:continue
        if u.id in w.vehicles and u.task_state=='HOVERING':
            vehicle=spec(w,u);u.fuel=max(0,u.fuel-vehicle['fuel_per_100m']*vehicle['speed_mps']*.2/100)
            if u.fuel<=0:damage_unit(w,u,u.hp,cause='fuel_exhaustion');continue
        target=engagement_target(w,u)
        u.target_id=None if target is None else target.id
        if target is None or u.cooldown_ms or u.type_id=='MBT' and u.task_state=='MOVING':continue
        attack=spec(w,u)['attack'];chance=attack['hit_probability']*(.8 if w.terrain.tile(target.pos.x_cm,target.pos.y_cm)==Tile.FOREST else 1)
        hit=w.rng.random()<chance;amount=round(attack['damage']*multiplier(w,u,target)) if hit else 0
        damage=min(target.hp,amount);u.ammo-=1;u.cooldown_ms=attack['interval_ms']
        if u.id in w.vehicles:u.turret_heading=atan2(target.pos.y_cm-u.pos.y_cm,target.pos.x_cm-u.pos.x_cm)
        impact=dict(x_cm=target.pos.x_cm,y_cm=target.pos.y_cm)
        splash=w.weapon_specs['tank_splash']
        plan=blast_plan(w,impact['x_cm'],impact['y_cm'],splash['blast_m']*100,splash['damage'],(target.id,)) if u.type_id=='MBT' and hit else []
        damage_unit(w,target,damage,u.id,'direct')
        if u.type_id=='MBT' and hit:
            w.emit('TANK_IMPACT',unit=u.id,target=target.id,**impact,blast_m=splash['blast_m'])
            for other,amount in plan:damage_unit(w,other,amount,u.id,'tank_splash')
        w.emit('ABSTRACT_ATTACK',unit=u.id,ammo=u.ammo,target=target.id,damage=damage,hit=hit,weapon=spec(w,u)['weapon'],origin=dict(x_cm=u.pos.x_cm,y_cm=u.pos.y_cm),destination=dict(x_cm=target.pos.x_cm,y_cm=target.pos.y_cm),range_m=attack['range_m'],distance_m=round(hypot(target.pos.x_cm-u.pos.x_cm,target.pos.y_cm-u.pos.y_cm)/100,2),hit_probability=chance,target_hp=target.hp)
    remaining=[]
    for shot in w.projectiles:
        if w.tick<shot['impact_tick']:remaining.append(shot);continue
        blast=w.weapon_specs['artillery']['blast_m']*100
        w.emit('ARTILLERY_IMPACT',**shot,blast_m=blast/100)
        for target,amount in blast_plan(w,shot['x_cm'],shot['y_cm'],blast,shot['damage']):damage_unit(w,target,amount,shot['unit'],'artillery')
    w.projectiles=remaining
