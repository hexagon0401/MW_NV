import pytest
from engine.scenario import create_match
from engine.runtime import Engine
from engine.orders import OrderError
from engine.types import Team,WorldPos,Command,Op
from engine.sensing import update_sensing
from agents.rule_hq import RuleHQ


def test_authenticated_queues_and_snapshots_do_not_cross_teams():
    e=Engine(create_match(9));a,b=e.observe(0),e.observe(1)
    assert not a['enemies'] and not b['enemies']
    assert not {u['id'] for u in a['units']} & {u['id'] for u in b['units']}
    cmd=RuleHQ().observe_and_issue(b)[0]
    with pytest.raises(OrderError,match='FOREIGN_TEAM'):e.submit_for(0,cmd)
    e.submit_for(1,cmd)
    assert not e.world.queue.commands.by_team['0']
    assert len(e.world.queue.commands.by_team['1'])==1
    a['resources']['supply']=-1
    assert e.world.teams[Team.A].supply==180
    hidden=e.world.soldiers[b['units'][0]['id']]
    hidden.pos=WorldPos(20000,20000)
    assert all(u['id']!=hidden.id for u in e.observe(0)['enemies'])


def test_swap_exactly_reflects_team_start_positions_and_resources():
    a,b=create_match(2),create_match(2,True)
    for id,s in a.soldiers.items():
        other=b.soldiers[id]
        assert s.team==other.team and s.pos.x_cm+other.pos.x_cm==25600
        assert s.pos.y_cm==other.pos.y_cm
    assert a.teams==b.teams
    assert a.terrain.cells==b.terrain.cells


def test_hold_stops_movement_and_invalid_dataclass_does_not_bypass_schema():
    e=Engine()
    with pytest.raises(OrderError,match='SCHEMA_ERROR'):
        e.submit(Command(1,Team.A,Op.MOVE,unit=1,arg0=2.5))
    e.submit_for(0,dict(cmd_id=1,team=0,op=2,unit=1,arg0=60,arg1=64));e.step(1)
    pos=e.world.soldiers[1].pos
    e.submit_for(0,dict(cmd_id=2,team=0,op=1,unit=1,tick=e.world.tick));e.step(1)
    assert e.world.soldiers[1].pos==pos and e.world.soldiers[1].task_state=='HOLD'


def test_policy_orders_are_private_and_low_fuel_is_serviced():
    e=Engine(create_match())
    truck=next(v for v in e.world.vehicles.values() if v.team==Team.A and v.type_id=='TRK')
    truck.fuel=10
    commands=RuleHQ().observe_and_issue(e.observe(0))
    assert len(commands)<=4 and commands[0]['op']==8 and commands[0]['unit']==truck.id
    e.submit_for(0,commands[0])
    assert len(e.observe(0)['orders'])==1 and e.observe(1)['orders']==[]


def test_future_order_does_not_cancel_current_movement_early():
    e=Engine()
    e.submit(dict(cmd_id=1,team=0,op=2,unit=1,arg0=60,arg1=64))
    e.step(1)
    e.submit(dict(cmd_id=2,team=0,op=1,unit=1,tick=10))
    e.step(1)
    assert e.world.soldiers[1].pos.x_cm==1120
    e.step(.2)
    assert e.world.soldiers[1].pos.x_cm==1120
    assert e.world.queue.status['0:1']=='CANCELLED'


@pytest.mark.parametrize('raw',[None,[], 'shell command'])
def test_non_command_input_fails_closed(raw):
    with pytest.raises(OrderError,match='SCHEMA_ERROR'):
        Engine().submit_for(0,raw)
