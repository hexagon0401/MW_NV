from engine.runtime import Engine
from engine.state import WorldState


def test_thousand_ticks_deterministic_and_partitioned_time():
    a, b = Engine(WorldState(8)), Engine(WorldState(8))
    for e in (a,b):
        e.submit(dict(cmd_id=1, team=0, op=0))
    a.step(200)
    for _ in range(2000):
        b.step(0.1)
    assert a.world.tick == 1000
    assert a.world.checksum() == b.world.checksum()
    assert sum(e['event_kind']=='ORDER_COMPLETED' for e in a.world.events) == 1


def test_cancel_before_execution():
    e = Engine()
    e.submit(dict(cmd_id=1,team=0,op=2,unit=1,arg0=20))
    e.submit(dict(cmd_id=2,team=0,op=12,target=1,priority=10))
    e.step()
    assert e.world.queue.status['0:1'] == 'CANCELLED'
    assert e.world.soldiers[1].pos.x_cm == 800
