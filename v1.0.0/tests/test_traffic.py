from engine.runtime import Engine
from engine.scenario import create_release_match
from engine.types import Vehicle,Team,WorldPos,Squad
from engine.traffic import arrival_slot
from engine.transport import FootprintTerrain
from engine.map import Terrain


def test_slots_are_distinct_legal_and_avoid_reserved_goals():
    e=Engine(create_release_match());obs=e.observe(0);goal=next(f['pos'] for f in obs['facilities'] if f['id']==202)
    a=obs['vehicles'][1];b=obs['vehicles'][2];sa=arrival_slot(obs,a,goal);assert sa
    obs['orders'].append(dict(unit=a['id'],op=7,status='RUNNING',arg0=sa[0],arg1=sa[1]))
    sb=arrival_slot(obs,b,goal);assert sb and sa!=sb


def test_wait_does_not_consume_fuel_or_fail_and_resumes_after_blocker_leaves():
    e=Engine();w=e.world;w.soldiers.clear();w.terrain=Terrain()
    # A narrow bridge-like corridor forces a wait rather than a nonexistent route failure.
    w.terrain.cells=[[6]*32 for _ in range(32)]
    for y in range(15,17):w.terrain.cells[y]=[1]*32
    w.vehicles[10]=Vehicle(10,Team.A,WorldPos(1000,6400));w.vehicles[11]=Vehicle(11,Team.A,WorldPos(2600,6400))
    e.submit(dict(cmd_id=1,team=0,op=7,unit=10,arg0=110,arg1=64));e.step(3)
    assert w.queue.status['0:1']=='RUNNING' and w.vehicles[10].task_state=='WAITING_TRAFFIC'
    pos=w.vehicles[10].pos;fuel=w.vehicles[10].fuel;e.step(.2);assert w.vehicles[10].pos==pos and w.vehicles[10].fuel==fuel
    w.vehicles[11].alive=False;e.step(30);assert w.vehicles[10].pos.x_cm==11000


def test_two_squads_board_carrier_in_fifo_order_without_overlap():
    from engine.catalog import make_soldier
    e=Engine();w=e.world;w.soldiers.clear();w.terrain=Terrain();v=Vehicle(50,Team.A,WorldPos(6000,6000),'HEL');w.vehicles[50]=v
    for j in range(2):
        ids=[]
        for i in range(2):
            uid=10+j*2+i;ids.append(uid);w.soldiers[uid]=make_soldier(uid,Team.A,WorldPos(5500-i*120,6000+j*120))
        w.squads[100+j]=Squad(100+j,Team.A,w.soldiers[ids[0]].pos,ids)
        e.submit(dict(cmd_id=j+1,team=0,op=5,unit=100+j,target=50))
    e.step(20)
    boarded=[ev['payload']['unit'] for ev in w.events if ev['event_kind']=='EMBARK_DONE']
    assert boarded==[10,11,12,13] and len(set(v.passenger_ids))==4


def test_active_boarding_reservation_survives_recent_order_history():
    e=Engine(create_release_match());w=e.world
    group=w.squads[10100];v=w.vehicles[10201]
    e.submit(dict(cmd_id=1,team=0,op=5,unit=group.id,target=v.id))
    for i in range(2,22):e.submit(dict(cmd_id=i,team=0,op=0))
    assert any(o['cmd_id']==1 and o['op']==5 for o in e.observe(0)['orders'])


def test_opposing_helicopters_reserve_different_landing_points():
    e=Engine();w=e.world;w.terrain=Terrain();w.soldiers.clear()
    w.vehicles[10]=Vehicle(10,Team.A,WorldPos(1000,2000),'HEL');w.vehicles[20]=Vehicle(20,Team.B,WorldPos(11000,10000),'HEL')
    for i,t in [(10,0),(20,1)]:e.submit(dict(cmd_id=1,team=t,op=7,unit=i,arg0=64,arg1=64))
    e.step(30)
    assert all(v.task_state=='ARRIVED' for v in w.vehicles.values())
    assert w.vehicles[10].pos!=w.vehicles[20].pos
    assert any(ev['event_kind']=='LANDING_DIVERTED' for ev in w.events)


def test_arrival_slots_mirror_physical_hq_sides():
    e=Engine(create_release_match(4));a=e.observe(0);b=e.observe(1)
    goal=next(f['pos'] for f in a['facilities'] if f['id']==202)
    pa=arrival_slot(a,a['vehicles'][1],goal);pb=arrival_slot(b,b['vehicles'][1],goal)
    assert pa and pb and pa[0]+pb[0]==1024 and pa[1]==pb[1]
