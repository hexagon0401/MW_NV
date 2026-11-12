import pytest
from engine.state import WorldState
from engine.runtime import Engine
from engine.types import Team,WorldPos,Vehicle
from engine.catalog import make_soldier
from engine.combat import blast_plan,damage_unit,tank_safe,update_combat
from engine.sensing import update_sensing


def world():
    w=WorldState(1);w.soldiers.clear();w.vehicles.clear();w.terrain.cells=[[0]*32 for _ in range(32)];Engine(w)
    w.vehicles[10]=Vehicle(10,Team.A,WorldPos(2000,6400),'MBT');return w


def test_blast_radius_falloff_armor_friendlies_air_and_passengers():
    w=world()
    for uid,x in [(1,5000),(2,5200),(3,5400)]:w.soldiers[uid]=make_soldier(uid,Team.B,WorldPos(x,6400))
    w.soldiers[4]=make_soldier(4,Team.A,WorldPos(5000,6400));w.soldiers[5]=make_soldier(5,Team.B,WorldPos(5000,6400));w.soldiers[5].carrier_id=20
    w.vehicles[20]=Vehicle(20,Team.B,WorldPos(5000,6400),'APC');w.vehicles[21]=Vehicle(21,Team.B,WorldPos(5000,6400),'HEL');w.vehicles[21].task_state='MOVING'
    planned={u.id:d for u,d in blast_plan(w,5000,6400,400,40)}
    assert planned=={1:40,2:20,4:40,20:28}
    for uid,amount in planned.items():damage_unit(w,w.soldiers.get(uid) or w.vehicles[uid],amount,10,'tank_splash')
    assert any(e['payload']['friendly_fire'] for e in w.events if e['event_kind']=='UNIT_DAMAGED')


def test_direct_target_not_double_hit_and_carrier_passenger_not_hit_twice():
    w=world();v=Vehicle(20,Team.B,WorldPos(5000,6400),'APC');v.hp=1;v.ammo=0;w.vehicles[20]=v
    passenger=make_soldier(1,Team.B,v.pos);passenger.carrier_id=20;w.soldiers[1]=passenger;v.passenger_ids=[1]
    w.vehicle_specs['MBT']['attack']['hit_probability']=1;update_sensing(w);update_combat(w)
    assert not v.alive and passenger.hp==75
    damages=[e['payload'] for e in w.events if e['event_kind']=='UNIT_DAMAGED']
    assert len([d for d in damages if d['unit']==20])==1
    assert len([d for d in damages if d['unit']==1])==1
    assert any(e['event_kind']=='TANK_IMPACT' for e in w.events)


def test_auto_target_friendly_risk_and_miss_has_no_splash():
    w=world();t=make_soldier(1,Team.B,WorldPos(5000,6400));w.soldiers[1]=t
    friend=make_soldier(2,Team.A,WorldPos(5100,6400));friend.ammo=0;w.soldiers[2]=friend
    assert not tank_safe(w,w.vehicles[10],t)
    update_sensing(w);update_combat(w);assert w.vehicles[10].ammo==30
    friend.pos=WorldPos(6000,6400);w.vehicle_specs['MBT']['attack']['hit_probability']=0;update_combat(w)
    assert not any(e['event_kind']=='TANK_IMPACT' for e in w.events)


def test_incompatible_engine_replay_rejected():
    from engine.replay import replay
    with pytest.raises(ValueError,match='incompatible'):replay(dict(version=2,rules_version='combined-arms-2',catalog_version='combined-arms-1'))
