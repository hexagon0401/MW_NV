import pytest
from engine.types import Vehicle,Team,WorldPos
from engine.runtime import Engine
from engine.replay import encode,decode
from engine.capabilities import airborne


def flight(team,kind='HEL'):
    from engine.catalog import expanded_catalog
    e=Engine();w=e.world;w.soldiers.clear();w.vehicles.clear();w.unit_specs,w.vehicle_specs,w.weapon_specs=expanded_catalog()
    # Wide river crossed by both teams: each destination is a legal landing pad.
    for cy in range(w.terrain.rows):
        for cx in range(14,18):w.terrain.set_tile(cx,cy,6)
    x=4000 if team==0 else 8800;v=Vehicle(20,Team(team),WorldPos(x,6400),kind);w.vehicles[v.id]=v
    target=100 if team==0 else 28
    def submit(id,**kw):e.submit_for(team,dict(cmd_id=id,team=team,unit=20,tick=w.tick,op=7,arg0=target,arg1=64,**kw))
    submit(1);e.step(6.2)
    assert w.terrain.tile(v.pos.x_cm,v.pos.y_cm)==6 and airborne(w,v)
    return e,v,submit,target

@pytest.mark.parametrize('team',[0,1])
@pytest.mark.parametrize('kind',['HEL','BH','LB'])
def test_retarget_above_water_keeps_airborne_and_lands(team,kind):
    e,v,submit,target=flight(team,kind);pos=v.pos;submit(2);e.step(.2)
    assert e.world.queue.status[f'{team}:1']=='CANCELLED';assert e.world.queue.status[f'{team}:2']=='RUNNING';assert v.pos!=pos
    e.step(30);assert v.task_state=='ARRIVED' and not airborne(e.world,v);assert v.pos==WorldPos(target*100,6400)

@pytest.mark.parametrize('team',[0,1])
def test_old_ready_checkpoint_recovers_without_teleport(team):
    e,v,submit,target=flight(team);w=e.world;w.queue.finish(w,f'{team}:1','CANCELLED');v.task_state='READY'
    clone=Engine(decode(encode(w)));original=v.pos;clone.step(.2);assert clone.world.vehicles[20].pos==original;assert clone.world.vehicles[20].task_state=='HOVERING'
    submit(2);e.step(30);assert v.task_state=='ARRIVED'


def test_hover_cannot_load_or_unload_and_is_not_fuel_free():
    from engine.types import Soldier
    e,v,submit,_=flight(0);w=e.world;w.queue.finish(w,'0:1','CANCELLED');fuel=v.fuel;s=Soldier(1,Team.A,v.pos);w.soldiers[1]=s
    e.submit_for(0,dict(cmd_id=2,team=0,unit=1,op=5,target=20,tick=w.tick));e.step(.2);assert w.queue.status['0:2']=='FAILED' and s.carrier_id is None
    s.carrier_id=20;v.passenger_ids=[1];e.submit_for(0,dict(cmd_id=3,team=0,unit=20,op=6,arg0=v.pos.x_cm//100,arg1=64,tick=w.tick));e.step(.2);assert w.queue.status['0:3']=='FAILED' and s.carrier_id==20
    assert v.fuel<fuel


def test_interrupted_flight_checkpoint_resumes_deterministically():
    e,v,submit,_=flight(0);e.world.queue.finish(e.world,'0:1','CANCELLED');v.task_state='READY';other=Engine(decode(encode(e.world)))
    command=dict(cmd_id=2,team=0,unit=20,op=7,arg0=100,arg1=64,tick=e.world.tick)
    for engine in (e,other):engine.submit_for(0,command);engine.step(30)
    assert e.world.checksum()==other.world.checksum()


def test_successful_landing_does_not_recover_an_older_cancelled_flight():
    e,v,submit,_=flight(0);submit(2);e.step(30);assert v.task_state=='ARRIVED'
    v.task_state='READY';e.step(.2);assert not airborne(e.world,v) and v.task_state=='READY'
