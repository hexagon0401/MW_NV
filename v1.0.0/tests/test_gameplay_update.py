from engine.runtime import Engine
from engine.state import WorldState
from engine.scenario import create_release_match
from engine.types import WorldPos,Squad,Team
from engine.viewer_export import frame
from agents.rule_hq import RuleHQ


def test_move_stops_at_range_and_attack_explains_damage():
    w=WorldState(15);w.soldiers[1].pos=WorldPos(1000,6400);w.soldiers[2].pos=WorldPos(2500,6400)
    w.soldiers[2].ammo=0;w.squads[50]=Squad(50,Team.A,w.soldiers[1].pos,[1])
    e=Engine(w);e.submit(dict(cmd_id=1,team=0,op=2,unit=50,arg0=25,arg1=64));e.step(4)
    assert w.soldiers[1].pos==WorldPos(1000,6400)
    assert w.soldiers[1].task_state=='ENGAGING'
    shots=[ev['payload'] for ev in w.events if ev['event_kind']=='ABSTRACT_ATTACK']
    assert shots and all(s['distance_m']==15 and s['range_m']==22 for s in shots)
    assert frame(w)['units'][0]['max_hp']==100


def test_expanded_release_roster_and_transport_orders():
    w=create_release_match(1);e=Engine(w)
    assert sum(s.team==0 for s in w.soldiers.values())==28
    # Place carrier near its intact eight-person squad.
    w.vehicles[1070].pos=WorldPos(12000,40000)
    commands=RuleHQ().observe_and_issue(e.observe(0))
    assert any(c['op']==5 for c in commands)
    assert w.facilities[203].supply_per_minute==8


def test_retreat_does_not_stop_to_engage():
    w=WorldState(15);w.soldiers[1].pos=WorldPos(2000,6400);w.soldiers[2].pos=WorldPos(3500,6400)
    w.squads[50]=Squad(50,Team.A,w.soldiers[1].pos,[1])
    e=Engine(w);e.submit(dict(cmd_id=1,team=0,op=10,unit=50,arg0=10,arg1=64));e.step()
    assert w.soldiers[1].pos.x_cm<2000
