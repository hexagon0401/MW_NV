import pytest
from engine.state import WorldState
from engine.runtime import Engine
from engine.types import Vehicle,WorldPos,Team,Command,Op
from engine.catalog import make_soldier
from engine.sensing import update_sensing
from engine.combat import damage_unit,fire_mission
from engine.orders import OrderError


def battle():
    w=WorldState(4);w.soldiers.clear();w.terrain.cells=[[0]*32 for _ in range(32)]
    w.soldiers[1]=make_soldier(1,Team.A,WorldPos(1000,6400),'AT',w.unit_specs)
    w.vehicles[20]=Vehicle(20,Team.B,WorldPos(9000,6400),'MBT')
    w.vehicles[20].ammo=0
    return Engine(w)


def test_armor_ranges_and_ammo():
    e=battle();w=e.world;update_sensing(w)
    # Rocket range 100m but target is outside own 40m detection.
    e.step();assert w.vehicles[20].hp==900
    w.vehicles[20].pos=WorldPos(4000,6400);e.step(12)
    assert w.vehicles[20].hp<900
    rocket_events=[ev for ev in w.events if ev['event_kind']=='ABSTRACT_ATTACK']
    assert rocket_events and all(ev['payload']['damage'] in (0,98) for ev in rocket_events)
    before=w.vehicles[20].hp;w.soldiers[1].type_id='INF';w.soldiers[1].ammo=20;w.soldiers[1].cooldown_ms=0
    w.vehicles[20].pos=WorldPos(2000,6400);e.step(4)
    assert w.vehicles[20].hp==before  # rifle cannot damage tank


def test_deploy_pack_and_observation_rejection():
    e=battle();w=e.world;w.vehicles[30]=Vehicle(30,Team.A,WorldPos(1000,1000),'SPH')
    e.submit(dict(cmd_id=1,team=0,op=15,unit=30));e.step(6)
    assert w.vehicles[30].deployment=='DEPLOYED'
    e.submit(dict(cmd_id=2,team=0,op=7,unit=30,arg0=20,arg1=10));e.step()
    assert w.queue.status['0:2']=='FAILED'
    c=Command(3,Team.A,Op.FIRE_MISSION,unit=30,arg0=120,arg1=100)
    with pytest.raises(OrderError,match='UNOBSERVED'):fire_mission(w,'x',c)
    e.submit(dict(cmd_id=4,team=0,op=16,unit=30));e.step(4)
    assert w.vehicles[30].deployment=='PACKED'


def test_artillery_seed_friendly_fire_and_expired_observation():
    from engine.config import GameConfig
    def shot():
        w=WorldState(7,GameConfig(512,512,.2));w.soldiers.clear();e=Engine(w)
        w.vehicles[30]=Vehicle(30,Team.A,WorldPos(1000,1000),'SPH');w.vehicles[30].deployment='DEPLOYED'
        w.visible={Team.A:[],Team.B:[]};w.last_seen={Team.A:{'99':dict(id=99,x_cm=15000,y_cm=1000,seen_at_tick=0)},Team.B:{}}
        c=Command(1,Team.A,Op.FIRE_MISSION,unit=30,arg0=150,arg1=10)
        fire_mission(w,'a',c);projectile=w.projectiles[0]
        w.soldiers[1]=make_soldier(1,Team.A,WorldPos(projectile['x_cm'],projectile['y_cm']))
        e.step(3.2)
        assert w.soldiers[1].hp==10
        return w
    assert shot().checksum()==shot().checksum()
    w=shot();w.tick=60;w.vehicles[30].cooldown_ms=0
    with pytest.raises(OrderError,match='UNOBSERVED'):fire_mission(w,'b',Command(2,Team.A,Op.FIRE_MISSION,unit=30,arg0=150,arg1=10))


def test_destroyed_carrier_evacuates_and_cannot_move():
    e=battle();w=e.world;v=w.vehicles[20];s=w.soldiers[1];s.team=Team.B;s.carrier_id=v.id;v.passenger_ids=[s.id]
    damage_unit(w,v,900,99)
    assert not v.alive and s.hp==65 and s.carrier_id is None and s.alive and not v.passenger_ids
    with pytest.raises(OrderError):e.submit(dict(cmd_id=5,team=1,op=7,unit=v.id,arg0=10,arg1=10))


@pytest.mark.parametrize('distance,valid',[(99,False),(100,True),(420,True),(421,False)])
def test_artillery_min_max_range_boundaries(distance,valid):
    from engine.config import GameConfig
    w=WorldState(7,GameConfig(512,512,.2));w.soldiers.clear();Engine(w)
    gun=Vehicle(30,Team.A,WorldPos(1000,1000),'SPH');gun.deployment='DEPLOYED';w.vehicles[30]=gun
    x=1000+distance*100;w.visible={Team.A:[],Team.B:[]};w.last_seen={Team.A:{'99':dict(id=99,x_cm=x,y_cm=1000,seen_at_tick=0)},Team.B:{}}
    c=Command(1,Team.A,Op.FIRE_MISSION,unit=30,arg0=x//100,arg1=10)
    if valid:assert fire_mission(w,'x',c)
    else:
        with pytest.raises(OrderError,match='OUT_OF_RANGE'):fire_mission(w,'x',c)


def test_flying_armor_and_empty_artillery_ammo():
    from engine.combat import multiplier
    e=battle();w=e.world;heli=Vehicle(40,Team.B,WorldPos(2000,6400),'HEL');w.vehicles[40]=heli;heli.task_state='MOVING'
    assert multiplier(w,w.soldiers[1],heli)==0
    w.soldiers[1].type_id='INF';assert multiplier(w,w.soldiers[1],heli)==.25
    heli.task_state='IDLE';assert multiplier(w,w.soldiers[1],heli)==.1
    w.vehicles[30]=Vehicle(30,Team.A,WorldPos(1000,1000),'SPH',ammo=0);w.vehicles[30].deployment='DEPLOYED'
    with pytest.raises(OrderError,match='NO_AMMO'):fire_mission(w,'x',Command(1,Team.A,Op.FIRE_MISSION,unit=30,arg0=120,arg1=100))
