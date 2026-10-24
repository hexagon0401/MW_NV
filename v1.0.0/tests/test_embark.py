from engine.runtime import Engine
from engine.types import Vehicle,Soldier,Squad,Team,WorldPos


def boarding_engine():
    e=Engine();w=e.world;w.soldiers.clear()
    w.vehicles[20]=Vehicle(20,Team.A,WorldPos(4000,6400))
    for i in range(1,6):w.soldiers[i]=Soldier(i,Team.A,WorldPos(3900+(i%3)*100,6300+(i//3)*100),ammo=0)
    w.squads[30]=Squad(30,Team.A,w.soldiers[1].pos,list(range(1,6)))
    return e


def test_timed_boarding_manifest_and_no_independent_motion():
    e=boarding_engine();w=e.world
    e.submit(dict(cmd_id=1,team=0,op=5,unit=30,target=20));e.step(.4)
    assert not w.vehicles[20].passenger_ids
    e.step(.2);assert len(w.vehicles[20].passenger_ids)==1
    e.step(2);assert len(w.vehicles[20].passenger_ids)==5
    assert all(s.pos==w.vehicles[20].pos and s.carrier_id==20 for s in w.soldiers.values())
    e.submit(dict(cmd_id=2,team=0,op=2,unit=1,arg0=70,arg1=64));e.step()
    assert w.queue.status['0:2']=='FAILED'


def test_capacity_foreign_team_and_reservations():
    e=boarding_engine();w=e.world
    w.vehicle_specs['APC']['capacity']=4
    e.submit(dict(cmd_id=1,team=0,op=5,unit=30,target=20));e.step()
    assert w.queue.status['0:1']=='FAILED' and not w.vehicles[20].passenger_ids
    w.vehicles[20].team=Team.B
    e.submit(dict(cmd_id=2,team=0,op=5,unit=30,target=20));e.step()
    assert w.events[-1]['payload']['reason']=='FOREIGN_UNIT'
