import pytest
from engine.orders import CommandQueue, OrderError
from engine.state import WorldState


def test_move_accepted():
    world, queue = WorldState(), CommandQueue()
    key = queue.submit(world, dict(cmd_id=1, team=0, op=2, unit=1, arg0=20, arg1=64))
    assert queue.status[key] == 'QUEUED'


@pytest.mark.parametrize('update,error', [({'unit':2}, 'FOREIGN_UNIT'),
    ({'arg0':128}, 'OUT_OF_BOUNDS'), ({'op':999}, 'UNKNOWN_OP'),
    ({'arg0':True}, 'SCHEMA_ERROR'), ({'shell':1}, 'SCHEMA_ERROR')])
def test_rejections(update, error):
    with pytest.raises(OrderError, match=error):
        CommandQueue().submit(WorldState(), dict(cmd_id=1, team=0, op=2, unit=1, arg0=20, arg1=64) | update)


def test_idempotency_priority_cancel_and_expiry():
    w, q = WorldState(), CommandQueue()
    raw = dict(cmd_id=1, team=0, op=2, unit=1, arg0=20, ttl=2)
    k = q.submit(w, raw)
    assert q.submit(w, raw) == k
    assert len(w.events) == 1
    second = q.submit(w, raw | dict(cmd_id=2, priority=2))
    assert q.ready(w)[0][0] == second
    q.cancel(w, 0, 1)
    assert all(key != k for key, _ in q.ready(w))
    w.tick = 2
    assert q.ready(w) == []
    assert q.status[second] == 'FAILED'
    assert q.status[k] == 'CANCELLED'
    assert w.soldiers[1].pos.x_cm == 800
    with pytest.raises(OrderError, match='INVALID_TARGET'):
        q.cancel(w, 1, 2)
