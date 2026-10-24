import pytest
from engine.runtime import Engine
from engine.logistics import debit,transfer_cargo
from engine.orders import OrderError
from engine.catalog import make_soldier
from engine.types import Team,Vehicle,WorldPos


def test_atomic_debit_and_truck_conservation():
    e=Engine();w=e.world;t=w.teams[Team.A]
    before=(t.supply,t.credits)
    with pytest.raises(OrderError):debit(w,Team.A,supply=1000,credits=1)
    assert (t.supply,t.credits)==before
    w.vehicles[20]=Vehicle(20,Team.A,WorldPos(800,6400),'TRK')
    transfer_cargo(w,20,120)
    assert t.supply==180 and w.vehicles[20].cargo_supply==120
    transfer_cargo(w,20,-120)
    assert t.supply==300 and w.vehicles[20].cargo_supply==0
    with pytest.raises(OrderError):transfer_cargo(w,20,121)


def test_resupply_timing_insufficient_and_healing_cap():
    e=Engine();w=e.world;s=w.soldiers[1];s.ammo=0
    e.submit(dict(cmd_id=1,team=0,op=8,unit=1,target=101));e.step(3.8)
    assert s.ammo==0
    e.step(.2);assert s.ammo==30 and w.teams[Team.A].supply==294
    w.soldiers[3]=make_soldier(3,Team.A,WorldPos(900,6400),'MED');s.hp=95
    e.submit(dict(cmd_id=2,team=0,op=9,unit=3,target=1,tick=w.tick));e.step(2)
    assert s.hp==100 and w.soldiers[3].heal_pool==75
    s.ammo=0;w.teams[Team.A].supply=0
    e.submit(dict(cmd_id=3,team=0,op=8,unit=1,target=101,tick=w.tick));e.step()
    assert w.queue.status['0:3']=='FAILED' and s.ammo==0
