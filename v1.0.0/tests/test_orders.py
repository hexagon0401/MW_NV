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
