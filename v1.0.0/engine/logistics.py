"""Atomic arcade resource transactions. Trucks hold deducted physical stock."""
from math import hypot,ceil,cos,sin
from .orders import OrderError
from .types import Team


def debit(w,team,**costs):
    state=w.teams[team]
    if any(name not in ('supply','credits','tickets') or type(value) is not int or value<0 for name,value in costs.items()):
        raise ValueError('invalid resource cost')
    if any(getattr(state,name)<value for name,value in costs.items()):
        raise OrderError('INSUFFICIENT_SUPPLY')
    for name,value in costs.items():setattr(state,name,getattr(state,name)-value)
    w.emit('SUPPLY_CHANGED',team=int(team),costs=costs)


def near(a,b,w=None):
    dx=a.pos.x_cm-b.pos.x_cm;dy=a.pos.y_cm-b.pos.y_cm
    from .catalog import load_vehicles
    footprints=w.vehicle_specs if w is not None else load_vehicles()
    if getattr(b,'type_id',None) in footprints:
        angle=getattr(b,'heading',0) or 0;rx=dx*cos(angle)+dy*sin(angle);ry=-dx*sin(angle)+dy*cos(angle);length,width=footprints[b.type_id]['footprint_cm'];dx=max(0,abs(rx)-length/2);dy=max(0,abs(ry)-width/2)
    return hypot(dx,dy)<=300


def transfer_cargo(w,truck_id,amount):
    truck=w.vehicles[truck_id]
    if not truck.alive or truck.type_id!='TRK' or type(amount) is not int or not any(f.kind in ('HQ','SUPPLY_NODE') and f.owner==truck.team and near(truck,f,w) for f in w.facilities.values()):
        raise OrderError('INVALID_TARGET')
    capacity=w.vehicle_specs['TRK']['cargo_capacity']
    if not 0<=truck.cargo_supply+amount<=capacity:
        raise OrderError('NO_CAPACITY')
    if amount>=0:debit(w,truck.team,supply=amount)
    else:w.teams[truck.team].supply-=amount
    truck.cargo_supply+=amount


def resupply(w,key,c):
    node=w.facilities.get(c.target) or w.vehicles.get(c.target)
    if node is None or getattr(node,'owner',getattr(node,'team',None))!=c.team:
        raise OrderError('INVALID_TARGET')
    if c.target in w.vehicles and (node.type_id!='TRK' or not node.alive):raise OrderError('INVALID_TARGET')
    if c.target in w.facilities and node.kind not in ('HQ','SUPPLY_NODE') and not getattr(node,'supply_per_minute',0):raise OrderError('INVALID_TARGET')
    ids=[i for i in w.squads[c.unit].member_ids if i not in w.soldiers or w.soldiers[i].alive] if c.unit in w.squads else [c.unit]
    units=[w.soldiers.get(i) or w.vehicles.get(i) for i in ids]
    if not units or any(u is None or not getattr(u,'alive',True) or u.team!=c.team or not near(u,node,w) or u.task_state in ('MOVING','ONBOARD') for u in units):
        raise OrderError('ILLEGAL_STATE')
    if not hasattr(w,'supply_timers'):w.supply_timers={}
    w.supply_timers[key]=w.supply_timers.get(key,0)+200
    changes=[];cost=0
    for u in units:
        if u.id in w.soldiers:
            spec=w.unit_specs[u.type_id]
            fields={'ammo':spec['ammo'],'heal_pool':spec['heal_pool'],'repair_pool':spec['repair_pool']}
            cost+=ceil(max(0,fields['ammo']-u.ammo)/10)*2+ceil(max(0,fields['heal_pool']-u.heal_pool)/10)+ceil(max(0,fields['repair_pool']-u.repair_pool)/10)
        else:
            fields={'fuel':w.vehicle_specs[u.type_id]['fuel_max'],'ammo':w.vehicle_specs[u.type_id]['ammo']}
            cost+=ceil(max(0,fields['fuel']-u.fuel)/10)*3+ceil(max(0,fields['ammo']-u.ammo)/10)*2
        changes.append((u,fields))
    stock=node.cargo_supply if c.target in w.vehicles else w.teams[c.team].supply
    if stock<cost:raise OrderError('INSUFFICIENT_SUPPLY')
    if w.supply_timers[key]<4000:return False
    if c.target in w.vehicles:
        node.cargo_supply-=cost;w.emit('SUPPLY_CHANGED',vehicle=node.id,cost=cost)
    else:debit(w,c.team,supply=cost)
    for u,fields in changes:
        for name,value in fields.items():setattr(u,name,value)
    return True


def heal(w,key,c):
    medic=w.soldiers.get(c.unit);target=w.soldiers.get(c.target)
    if medic is None or target is None or medic.type_id!='MED' or target.team!=c.team or not medic.alive or not target.alive or medic.carrier_id is not None or target.carrier_id is not None or not near(medic,target,w):
        raise OrderError('INVALID_TARGET')
    if medic.task_state=='MOVING' or target.task_state=='MOVING':raise OrderError('ILLEGAL_STATE')
    missing=w.unit_specs[target.type_id]['hp']-target.hp
    if missing<=0:return True
    amount=min(8,missing,medic.heal_pool)
    if amount<=0 or w.teams[c.team].supply<ceil(amount/10):raise OrderError('INSUFFICIENT_SUPPLY')
    if not hasattr(w,'heal_timers'):w.heal_timers={}
    w.heal_timers[key]=w.heal_timers.get(key,0)+200
    if w.heal_timers[key]>=2000:
        w.heal_timers[key]-=2000
        debit(w,c.team,supply=ceil(amount/10));medic.heal_pool-=amount;target.hp+=amount
        w.emit('UNIT_HEALED',unit=target.id,amount=amount)
    return target.hp==w.unit_specs[target.type_id]['hp']


def regenerate(w):
    from .scenario_spec import rules
    if not rules(w)['regenerate_supply']:return
    if (w.tick+1)%300==0:
        for team in Team:
            amount=3+sum(getattr(f,'supply_per_minute',0) for f in w.facilities.values() if f.owner==team)
            w.teams[team].supply+=amount
            w.emit('SUPPLY_CHANGED',team=int(team),amount=amount)


def repair(w,key,c):
    eng=w.soldiers.get(c.unit);target=w.vehicles.get(c.target)
    if eng is None or eng.type_id!='ENG' or not eng.alive or eng.carrier_id is not None or target is None or target.team!=c.team or not target.alive or not near(eng,target,w):raise OrderError('INVALID_TARGET')
    if eng.task_state=='MOVING' or target.task_state in ('MOVING','TAKEOFF','LANDING'):raise OrderError('ILLEGAL_STATE')
    missing=w.vehicle_specs[target.type_id]['hp']-target.hp
    if missing<=0:return True
    if eng.repair_pool<10 or w.teams[c.team].supply<2:raise OrderError('INSUFFICIENT_SUPPLY')
    if not hasattr(w,'repair_timers'):w.repair_timers={}
    w.repair_timers[key]=w.repair_timers.get(key,0)+200
    if w.repair_timers[key]>=2000:
        w.repair_timers[key]-=2000;debit(w,c.team,supply=2);eng.repair_pool-=10;target.hp+=min(10,missing)
        w.emit('UNIT_REPAIRED',unit=target.id,amount=min(10,missing),hp=target.hp)
    return target.hp==w.vehicle_specs[target.type_id]['hp']
