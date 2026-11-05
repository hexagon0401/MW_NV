from engine.runtime import Engine
from engine.types import Team
from engine.logistics import resupply
from engine.types import Command,Op

def test_partial_ammo_finite_stock_and_authoritative_event():
    e=Engine();w=e.world;u=w.soldiers[1];u.ammo=0;w.teams[Team.A].supply=2
    e.submit(dict(cmd_id=1,team=0,op=8,unit=1,target=101));e.step(4)
    assert u.ammo==10 and w.teams[Team.A].supply==0
    assert any(x['event_kind']=='UNIT_RESUPPLIED' and x['payload']['ammo']==10 for x in w.events)

def test_truck_reload_conserves_team_stock():
    from engine.types import Vehicle,WorldPos
    e=Engine();w=e.world;truck=Vehicle(20,Team.A,WorldPos(800,6400),'TRK');w.vehicles[20]=truck
    before=w.teams[Team.A].supply
    e.submit(dict(cmd_id=1,team=0,op=8,unit=20,target=101));e.step(4)
    assert truck.cargo_supply==240 and w.teams[Team.A].supply==before-240

def test_resupply_suppresses_fire_until_completion():
    from engine.types import WorldPos
    e=Engine();w=e.world;u=w.soldiers[1];u.ammo=1
    enemy=next(s for s in w.soldiers.values() if s.team!=u.team);enemy.pos=WorldPos(u.pos.x_cm+100,u.pos.y_cm)
    e.submit(dict(cmd_id=1,team=0,op=8,unit=1,target=101));e.step(3.8)
    assert u.ammo==1 and not any(x['event_kind']=='ABSTRACT_ATTACK' and x['payload']['unit']==1 for x in w.events)
