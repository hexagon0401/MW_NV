from engine.runtime import Engine


def test_distance_completion_and_cancel():
    e = Engine()
    e.submit(dict(cmd_id=1,team=0,op=2,unit=1,arg0=80,arg1=64,ttl=2000))
    e.step(10)
    assert e.world.soldiers[1].pos.x_cm == 2400
    e.step(40)
    assert e.world.soldiers[1].pos.x_cm == 8000
    assert sum(x['event_kind']=='ORDER_COMPLETED' for x in e.world.events)==1
    assert e.world.queue.status['0:1']=='COMPLETED'
    e.submit(dict(cmd_id=2,team=0,op=2,unit=1,arg0=90,arg1=64,tick=e.world.tick))
    e.world.queue.cancel(e.world,0,2)
    e.step(1)
    assert e.world.soldiers[1].pos.x_cm==8000


def test_dynamic_wall_blocks_without_replanning_each_tick():
    e = Engine()
    e.submit(dict(cmd_id=1,team=0,op=2,unit=1,arg0=80,arg1=64))
    e.step(1)
    e.world.terrain.set_tile(3,16,3)
    e.step(5)
    assert e.world.motions['0:1']['rerouted']
    s=e.world.soldiers[1]
    assert e.world.terrain.passable(s.pos.x_cm,s.pos.y_cm)
