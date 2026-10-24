import pytest
from engine.runtime import Engine
from engine.map import Terrain
from engine.types import Vehicle,Team,WorldPos


def vehicle_engine(road=True):
    e=Engine();w=e.world;w.terrain=Terrain();w.soldiers.clear()
    if road:w.terrain.cells=[[1]*32 for _ in range(32)]
    w.vehicles[10]=Vehicle(10,Team.A,WorldPos(1000,6400))
    return e


def test_road_fuel_and_grass_speed():
    e=vehicle_engine();e.submit(dict(cmd_id=1,team=0,op=7,unit=10,arg0=110,arg1=64));e.step(20)
    v=e.world.vehicles[10]
    assert v.pos.x_cm==11000 and v.fuel==pytest.approx(97)
    e=vehicle_engine(False);e.submit(dict(cmd_id=1,team=0,op=7,unit=10,arg0=110,arg1=64));e.step(10)
    assert e.world.vehicles[10].pos.x_cm==4850


def test_no_fuel_and_vehicle_overlap_and_narrow_route():
    e=vehicle_engine();v=e.world.vehicles[10];v.fuel=0
    e.submit(dict(cmd_id=1,team=0,op=7,unit=10,arg0=100,arg1=64));e.step()
    assert v.pos.x_cm==1000 and e.world.queue.status['0:1']=='FAILED'
    e=vehicle_engine();e.world.vehicles[11]=Vehicle(11,Team.A,WorldPos(2500,6400))
    e.submit(dict(cmd_id=1,team=0,op=7,unit=10,arg0=100,arg1=64));e.step(10)
    assert e.world.vehicles[10].pos.x_cm<=1800
    assert not hasattr(e.world.vehicles[10],'attack')
    assert set(e.world.vehicle_specs)=={'LUV','APC','IFV','HEL','TRK'}
