import asyncio,json
from threading import Event
import pytest
pytest.importorskip('fastapi');pytest.importorskip('httpx')
from fastapi.testclient import TestClient
from server.live import LiveRunner,stream
from server.app import create_app
from engine.runtime import Engine
from engine.state import WorldState
from engine.viewer_export import frame,export_view


def test_snapshots_are_detached_and_observation_does_not_change_determinism():
    world=WorldState(5);engine=Engine(world);reference=Engine(world.clone());runner=LiveRunner(engine)
    for _ in range(100):runner.advance()
    reference.step(20)
    assert engine.world.checksum()==reference.world.checksum()
    snapshot=runner.snapshot(True);snapshot['frame']['units'][0]['size_px'][0]=999
    snapshot['terrain'][0][0]=9
    assert engine.world.unit_specs['INF']['size_px'][0]==12
    assert engine.world.checksum()==reference.world.checksum()
    assert engine.observe(0)['enemies']==[]
    assert len(runner.snapshot()['frame']['units'])==2


def test_live_routes_are_local_admin_only_and_do_not_expose_unfinished_matches(tmp_path):
    runner=LiveRunner(Engine())
    app=create_app(tmp_path,live_runner=runner)
    client=TestClient(app,base_url='http://127.0.0.1')
    assert client.get('/api/live/snapshot').status_code==200
    assert client.get('/api/matches').json()==[]
    assert client.post('/api/live/snapshot').status_code==405
    assert client.get('/api/live/snapshot',headers={'origin':'https://evil.example'}).status_code==403
    assert client.get('/api/live/snapshot',headers={'host':'evil.example'}).status_code==403
    assert TestClient(create_app(tmp_path)).get('/api/live/snapshot').status_code==404


def test_sse_bootstrap_update_reconnect_and_stop():
    class Request:
        async def is_disconnected(self):return False
    async def run():
        runner=LiveRunner(Engine());iterator=stream(runner,Request())
        first=await anext(iterator);assert 'event: snapshot' in first and 'terrain' in first
        runner.advance();second=await anext(iterator);assert 'event: state' in second
        body=json.loads(second.split('data: ',1)[1]);assert body['frame']['tick']==1
        reconnect=stream(runner,Request());latest=await anext(reconnect)
        assert json.loads(latest.split('data: ',1)[1])['seq']==runner.seq
        await reconnect.aclose();runner.stop();last=await anext(iterator)
        assert json.loads(last.split('data: ',1)[1])['status']=='stopped'
        with pytest.raises(StopAsyncIteration):await anext(iterator)
    asyncio.run(run())


def test_llm_barrier_freezes_clock_and_publishes_waiting_state():
    entered,release=Event(),Event();runner=LiveRunner(Engine(),hq='local');calls=[]
    def answer(payload):
        calls.append(json.loads(payload['messages'][1]['content'])['team'])
        entered.set();release.wait(2);return '{"commands":[]}'
    for policy in runner.policies.values():policy.transport=answer
    try:
        runner.start();assert entered.wait(1)
        waiting=runner.snapshot();assert waiting['status']=='waiting_for_hq' and waiting['frame']['tick']==0
        release.set();running=runner.wait_after(waiting['seq'],2)
        assert running['status']=='running' and running['frame']['tick']>=1
        assert calls==[0,1]
    finally:release.set();runner.stop()


def test_export_enriches_only_copies_and_completed_live_game_is_archived(tmp_path):
    e=Engine();initial=frame(e.world)
    e.submit(dict(cmd_id=1,team=0,op=2,unit=1,arg0=80,arg1=64));e.step(3000)
    checksum=e.world.checksum();doc=export_view(e,initial)
    assert e.world.checksum()==checksum
    original=next(x for x in e.world.events if x['event_kind']=='ORDER_ACCEPTED')
    enriched=next(x for x in doc['events'] if x['event_kind']=='ORDER_ACCEPTED')
    assert 'op' not in original['payload'] and enriched['payload']['op']==2
    doc['terrain'][0][0]=9;doc['initial']['units'][0]['size_px'][0]=999
    assert e.world.checksum()==checksum
    engine=Engine();engine.world.tick=14999
    runner=LiveRunner(engine,output_dir=tmp_path);runner.advance()
    assert runner.snapshot()['status']=='ended'
    assert len(list(tmp_path.glob('*.view.json')))==1
    assert TestClient(create_app(tmp_path)).get('/matches').json()[0]['summary']['ended']


def test_live_rules_and_readside_exports_match_unobserved_game_commands():
    from engine.scenario import create_match
    from engine.types import Team
    from agents.rule_hq import RuleHQ
    world=create_match(7);runner=LiveRunner(Engine(world));reference=Engine(world.clone());policy=RuleHQ()
    for _ in range(151):
        if reference.world.tick%150==0:
            observations={t:reference.observe(t) for t in Team}
            for t in Team:
                for command in policy.observe_and_issue(observations[t]):reference.submit_for(t,command)
        runner.advance();reference.step(.2)
    assert runner.engine.world.checksum()==reference.world.checksum()
    a=runner.engine.observe(0);b=runner.engine.observe(1)
    a_ids={u['id'] for u in a['units']+a['vehicles']}
    b_ids={u['id'] for u in b['units']+b['vehicles']}
    assert not a_ids&b_ids
    assert a_ids|b_ids=={u['id'] for u in runner.snapshot()['frame']['units']}
