from engine.scenario import create_release_match
from engine.replay import RecordingEngine,replay
from engine.runtime import Engine
from engine.transport import FootprintTerrain
from engine.pathfinding import find_path
from engine.sensing import update_sensing
from agents.tactics import TacticalHQ


def test_armor_routes_connect_spawn_to_all_objectives():
    w=create_release_match(11)
    assert all(row==list(reversed(row)) for row in w.terrain.cells)
    for team in (0,1):
        tank=next(v for v in w.vehicles.values() if v.type_id=='MBT' and v.team==team)
        terrain=FootprintTerrain(w.terrain,w.vehicle_specs['MBT']['footprint_cm'])
        for f in w.facilities.values():
            if f.kind=='OBJECTIVE':assert find_path(terrain,(tank.pos.x_cm,tank.pos.y_cm),(f.pos.x_cm,f.pos.y_cm),True)


def test_new_release_recording_replays_and_spectator_read_is_pure():
    from engine.viewer_export import frame
    from engine.orders import OrderError
    e=RecordingEngine(create_release_match(2));policies=[TacticalHQ(),TacticalHQ()]
    for _ in range(2):
        for t in (0,1):
            for command in policies[t].observe_and_issue(e.observe(t)):e.submit_for(t,command)
        e.step(2)
        checksum=e.world.checksum();frame(e.world)
        assert e.world.checksum()==checksum
    assert replay(e.document()).checksum()==e.world.checksum()


def test_expired_vehicle_order_releases_moving_state():
    e=Engine(create_release_match());v=next(v for v in e.world.vehicles.values() if v.type_id=='MBT' and v.team==0)
    e.submit(dict(cmd_id=1,team=0,op=7,unit=v.id,arg0=512,arg1=224,ttl=1));e.step(.4)
    assert e.world.queue.status['0:1']=='FAILED' and v.task_state!='MOVING'


def test_individual_order_replaces_overlapping_squad_movement():
    e=Engine(create_release_match());w=e.world;group=w.squads[10104]
    eng=next(w.soldiers[i] for i in group.member_ids if w.soldiers[i].type_id=='ENG')
    e.submit(dict(cmd_id=1,team=0,op=2,unit=group.id,arg0=512,arg1=224));e.step()
    e.submit(dict(cmd_id=2,team=0,op=1,unit=eng.id,tick=w.tick));e.step()
    assert w.queue.status['0:1']=='CANCELLED' and eng.task_state=='HOLD'


def test_casualties_do_not_prevent_surviving_squad_embark():
    from engine.types import WorldPos
    e=Engine(create_release_match());w=e.world;g=w.squads[10100];v=w.vehicles[10201]
    w.soldiers[g.member_ids[0]].alive=False
    for i in g.member_ids[1:]:w.soldiers[i].pos=WorldPos(v.pos.x_cm-100,v.pos.y_cm)
    e.submit(dict(cmd_id=1,team=0,op=5,unit=g.id,target=v.id));e.step(4)
    assert len(v.passenger_ids)==7
