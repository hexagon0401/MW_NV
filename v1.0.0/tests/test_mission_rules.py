from engine.multi_scenario import create
from engine.mission_rules import update,combat_possible
from engine.types import Team,WorldPos

def test_expanded_rosters_and_geometry():
    for identity,width in [('3',1536),('4',2304)]:
        w=create(17,scenario_id=identity);assert w.config.map_width_m==width
        for team in Team:
            assert sum(s.team==team for s in w.soldiers.values())==96
            assert sum(v.team==team for v in w.vehicles.values())==16
        assert all(w.terrain.passable(s.pos.x_cm,s.pos.y_cm) for s in w.soldiers.values())
        assert len([v for v in w.vehicles.values() if v.team is None])==(4 if identity=='3' else 2)

def test_exhaustion_not_just_zero_supply_and_simultaneous_tie():
    w=create(scenario_id='3');w.teams[Team.A].supply=0;assert combat_possible(w,Team.A)
    for u in [*w.soldiers.values(),*w.vehicles.values()]:u.alive=False
    for t in Team:w.teams[t].credits=0;w.teams[t].tickets=0
    update(w);assert w.ended and w.winner is None

def test_flag_requires_inside_dismounted_then_return_home():
    w=create(scenario_id='4');enemy=w.flags[1];troops=[s for s in w.soldiers.values() if s.team==0][:3];pos=w.facilities[102].pos
    for s in troops:s.pos=pos
    for _ in range(75):update(w);w.tick+=1
    assert enemy['status']=='carried' and enemy['carrier']==min(s.id for s in troops)
    carrier=w.soldiers[enemy['carrier']];carrier.carrier_id=10200;carrier.pos=w.facilities[101].pos
    for _ in range(30):update(w);w.tick+=1
    assert not getattr(w,'ended',False)
    carrier.carrier_id=None
    for _ in range(25):update(w);w.tick+=1
    assert w.ended and w.winner==Team.A

def test_hidden_carrier_position_and_id_not_in_observation():
    from engine.runtime import Engine
    w=create(scenario_id='4');carrier=next(s for s in w.soldiers.values() if s.team==1);f=w.flags[0];f.update(status='carried',carrier=carrier.id,x_cm=carrier.pos.x_cm,y_cm=carrier.pos.y_cm)
    e=Engine(w);before=e.observe(0)['mission'];carrier.pos=WorldPos(carrier.pos.x_cm+100,carrier.pos.y_cm);f.update(x_cm=carrier.pos.x_cm)
    assert before==e.observe(0)['mission'];assert before['flags'][0]['carrier'] is None

def test_carrier_speed_and_water_drop_auto_return():
    from engine.mission_actions import speed
    w=create(scenario_id='4');s=next(s for s in w.soldiers.values() if s.team==0);f=w.flags[1];f.update(status='carried',carrier=s.id)
    assert speed(w,s,2)==1.7
    s.alive=False;s.pos=WorldPos(40000,40000);update(w);assert f['status']=='dropped'
    w.tick+=300;update(w);assert f['status']=='home'

def test_wall_blocks_direct_room_entry_but_doors_are_reachable():
    from engine.pathfinding import find_path
    from engine.transport import FootprintTerrain
    w=create(scenario_id='4');base=w.bases[0];hq=w.facilities[101];start=(hq.pos.x_cm+5000,hq.pos.y_cm)
    assert not w.terrain.segment_clear(start,(hq.pos.x_cm,hq.pos.y_cm))
    assert find_path(w.terrain,start,(hq.pos.x_cm,hq.pos.y_cm))
    assert not FootprintTerrain(w.terrain,[900,450]).passable(hq.pos.x_cm,hq.pos.y_cm)
