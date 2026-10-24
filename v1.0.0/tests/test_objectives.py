from engine.runtime import Engine
from engine.types import Soldier,Team,WorldPos,Facility


def capture_engine(n=3,owner=None):
    e=Engine();w=e.world;w.soldiers.clear()
    for i in range(n):
        w.soldiers[i+1]=Soldier(i+1,Team.A,WorldPos(6000+i*100,6400),ammo=0)
    w.facilities={100:Facility(100,WorldPos(6400,6400),owner=owner)}
    return e


def test_capture_exact_boundary_and_neutralization():
    e=capture_engine();e.step(19.8)
    assert e.world.facilities[100].owner is None
    e.step(.2);assert e.world.facilities[100].owner==Team.A
    assert sum(x['event_kind']=='OBJECTIVE_CAPTURED' for x in e.world.events)==1
    e=capture_engine(owner=Team.B);e.step(15)
    assert e.world.facilities[100].owner is None
    e.step(20);assert e.world.facilities[100].owner==Team.A


def test_insufficient_contested_and_onboard():
    e=capture_engine(2);e.step(21);assert e.world.facilities[100].owner is None
    e=capture_engine();e.world.soldiers[4]=Soldier(4,Team.B,WorldPos(6400,6500),ammo=0)
    e.step(25);assert e.world.facilities[100].progress_ms==0
    e=capture_engine();e.world.soldiers[1].carrier_id=999
    e.step(25);assert e.world.facilities[100].owner is None
