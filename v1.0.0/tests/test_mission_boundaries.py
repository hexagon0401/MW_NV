import pytest
from engine.multi_scenario import create
from engine.mission_rules import update,combat_possible
from engine.types import Team,WorldPos
from engine.runtime import Engine
from engine.combat import damage_unit
from engine.replay import encode,decode

@pytest.fixture
def flagworld():return create(3,scenario_id='4')

def test_steal_pauses_contested_and_resets_when_empty(flagworld):
    w=flagworld;attackers=[s for s in w.soldiers.values() if s.team==0][:3];defender=next(s for s in w.soldiers.values() if s.team==1);room=w.facilities[102].pos;f=w.flags[1]
    for s in attackers:s.pos=room
    for _ in range(20):update(w);w.tick+=1
    assert f['progress_ms']==4000
    defender.pos=room
    for _ in range(10):update(w);w.tick+=1
    assert f['progress_ms']==4000
    for s in attackers:s.pos=WorldPos(30000,30000)
    update(w);assert f['progress_ms']==0 and f['status']=='home'


def test_air_carrier_destruction_does_not_duplicate_flag_or_win(flagworld):
    w=flagworld;u=next(s for s in w.soldiers.values() if s.team==0);v=next(v for v in w.vehicles.values() if v.team==0 and v.type_id=='BH');v.task_state='HOVERING';u.carrier_id=v.id;u.pos=v.pos;u.hp=20;v.passenger_ids=[u.id];w.flags[1].update(status='carried',carrier=u.id,x_cm=u.pos.x_cm,y_cm=u.pos.y_cm)
    damage_unit(w,v,v.hp);update(w)
    assert not u.alive and w.flags[1]['status']=='dropped' and w.flags[1]['carrier'] is None;assert not getattr(w,'ended',False)
    assert len([e for e in w.events if e['event_kind']=='FLAG_DROPPED'])==1


def test_mounted_troops_and_weapons_cannot_steal(flagworld):
    w=flagworld;people=[s for s in w.soldiers.values() if s.team==0][:3]
    for s in people:s.pos=w.facilities[102].pos;s.carrier_id=10200
    for _ in range(80):update(w);w.tick+=1
    assert w.flags[1]['status']=='home' and not getattr(w,'ended',False)
    w.tick=17999;update(w);assert w.ended and w.winner is None and w.termination_reason=='TIME_LIMIT_DRAW'


def test_hidden_changes_do_not_change_candidates(flagworld):
    from agents.mission_tactics import candidates
    w=flagworld;e=Engine(w);before=candidates(e.observe(0));enemy=next(s for s in w.soldiers.values() if s.team==1);enemy.pos=WorldPos(enemy.pos.x_cm-1200,enemy.pos.y_cm);w.teams[1].credits+=2000
    w.flags[0].update(status='carried',carrier=enemy.id,x_cm=enemy.pos.x_cm,y_cm=enemy.pos.y_cm)
    # Public status can change candidates; subsequent hidden movement cannot.
    before=candidates(e.observe(0));enemy.pos=WorldPos(enemy.pos.x_cm+400,enemy.pos.y_cm);w.flags[0]['x_cm']=enemy.pos.x_cm
    assert before==candidates(e.observe(0))


def test_new_mode_checkpoint_determinism(flagworld):
    a=Engine(flagworld);b=Engine(decode(encode(flagworld)));a.step(2);b.step(2);assert a.world.checksum()==b.world.checksum()


def test_elimination_affordable_armed_reinforcement_and_unarmed_defeat():
    w=create(2,scenario_id='3')
    for u in [*w.soldiers.values(),*w.vehicles.values()]:u.alive=False
    w.teams[0].credits=1000;w.teams[0].tickets=1;w.teams[1].credits=0;w.teams[1].tickets=0
    assert combat_possible(w,0);update(w);assert w.ended and w.winner==0
