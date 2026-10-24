from engine.runtime import Engine
from engine.types import WorldPos,Team
from engine.sensing import update_sensing


def test_recon_distance_wall_forest_and_stale_expiry():
    e=Engine();w=e.world;a,b=w.soldiers.values()
    a.pos=WorldPos(1000,6400);b.pos=WorldPos(5000,6400)
    update_sensing(w);assert not e.observe(0)['enemies']
    a.type_id='REC';update_sensing(w);assert e.observe(0)['enemies'][0]['id']==2
    w.terrain.set_tile(8,16,3);update_sensing(w)
    assert not e.observe(0)['enemies']
    assert e.observe(0)['last_seen'][0]['x_cm']==5000
    b.pos=WorldPos(9000,6400);w.tick=300;update_sensing(w)
    assert not e.observe(0)['last_seen']
    w.terrain.set_tile(8,16,1);w.terrain.set_tile(2,16,2);w.terrain.set_tile(12,16,2)
    b.pos=WorldPos(5000,6400);update_sensing(w)
    assert not e.observe(0)['enemies']


def test_observations_are_detached_and_hidden_units_absent():
    e=Engine();obs=e.observe(Team.A)
    assert [s['id'] for s in obs['units']]==[1]
    assert obs['enemies']==[]
    obs['units'][0]['pos']['x_cm']=9999
    assert e.world.soldiers[1].pos.x_cm==800
