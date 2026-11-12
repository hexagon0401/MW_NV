"""Training-only domain randomization with independent RNG and legal spawn fallback."""
import random
from engine.multi_scenario import create as base
from engine.transport import FootprintTerrain
from engine.types import WorldPos


def create(seed=0,swap=False,scenario_id='2',spawn_radius_m=32):
    if spawn_radius_m not in (32,64):raise ValueError('unsupported curriculum radius')
    w=base(seed,swap,scenario_id=scenario_id);rng=random.Random(seed^0x53545241)
    multiplier=rng.uniform(.8,1.2)
    for key in ('credits','tickets','supply'):
        value=round(w.scenario[key]*multiplier);w.scenario[key]=value
        for team in w.teams.values():setattr(team,key,value)
    protected=set()
    for collection in (w.soldiers,w.vehicles,w.facilities):
        for u in collection.values():protected.add((u.pos.x_cm//400,u.pos.y_cm//400))
    # Only thin existing forest; do not close routes or modify collision structures.
    for y,row in enumerate(w.terrain.cells):
        for x,t in enumerate(row):
            if t==2 and (x,y) not in protected and rng.random()<.12:row[x]=0
    offsets={}
    for team in (0,1):
        units=[u for u in [*w.soldiers.values(),*w.vehicles.values()] if u.team==team]
        chosen=(0,0)
        for _ in range(32):
            dx=rng.randint(-spawn_radius_m,spawn_radius_m)*100;dy=rng.randint(-spawn_radius_m,spawn_radius_m)*100
            def legal(u):
                if u.id in w.vehicles:
                    spec=w.vehicle_specs[u.type_id]
                    return FootprintTerrain(w.terrain,spec['footprint_cm']).passable(u.pos.x_cm+dx,u.pos.y_cm+dy)
                return w.terrain.passable(u.pos.x_cm+dx,u.pos.y_cm+dy)
            if all(legal(u) for u in units):chosen=(dx,dy);break
        for u in units+[s for s in w.squads.values() if s.team==team]:u.pos=WorldPos(u.pos.x_cm+chosen[0],u.pos.y_cm+chosen[1])
        offsets[str(team)]=list(chosen)
    w.training_variant=dict(version='domain-1',spawn_radius_m=spawn_radius_m,spawn_offsets=offsets,resource_multiplier=multiplier)
    w.terrain.revision+=1;w.terrain.cache.clear()
    return w


def factory(scenario_id):
    return lambda seed,swap=False:create(seed,swap,scenario_id)
