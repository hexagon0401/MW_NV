import pytest
from test_embark import boarding_engine


@pytest.mark.parametrize('kind', ['APC','HEL'])
def test_full_transport_end_to_end(kind):
    e=boarding_engine();w=e.world;v=w.vehicles[20];v.type_id=kind
    e.submit(dict(cmd_id=1,team=0,op=5,unit=30,target=20));e.step(3)
    e.submit(dict(cmd_id=2,team=0,op=7,unit=20,arg0=80,arg1=64,tick=w.tick))
    if kind=='HEL':
        start=v.pos;e.step(4);assert v.pos==start
    e.step(30)
    assert v.pos.x_cm==8000 and v.task_state=='ARRIVED'
    assert all(s.pos==v.pos for s in w.soldiers.values())
    e.submit(dict(cmd_id=3,team=0,op=6,unit=20,arg0=80,arg1=64,tick=w.tick));e.step(3)
    assert not v.passenger_ids
    assert len({s.pos for s in w.soldiers.values()})==5
    assert all(s.carrier_id is None and w.terrain.passable(s.pos.x_cm,s.pos.y_cm) for s in w.soldiers.values())


def test_bad_heli_landing():
    e=boarding_engine();w=e.world;w.vehicles[20].type_id='HEL'
    w.terrain.set_tile(20,16,3)
    e.submit(dict(cmd_id=1,team=0,op=7,unit=20,arg0=80,arg1=64));e.step()
    assert w.queue.status['0:1']=='FAILED'
    assert w.events[-1]['payload']['reason']=='LANDING_INVALID'
