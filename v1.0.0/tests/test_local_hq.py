import json
import pytest
from agents.local_hq import LocalHQ,issue_hq_round
from engine.runtime import Engine
from engine.scenario import create_match
from engine.types import Team


def test_two_team_barrier_and_invalid_owner_fallback():
    e=Engine(create_match());seen=[]
    def respond(payload):
        obs=json.loads(payload['messages'][1]['content']);seen.append((obs,e.world.tick))
        return json.dumps({'commands':[{'op':1,'unit':obs['units'][0]['id']}]})
    policies={t:LocalHQ(transport=respond) for t in Team}
    issue_hq_round(e,policies)
    assert [tick for obs,tick in seen]==[0,0]
    assert not set(u['id'] for u in seen[0][0]['units'])&set(u['id'] for u in seen[1][0]['units'])
    e.step(.2);assert e.world.tick==1
    policies[Team.A].transport=lambda _:json.dumps({'commands':[{'op':1,'unit':1101}]})
    issue_hq_round(e,policies)
    assert policies[Team.A].last_decision['fallback_reason']=='INVALID_GAME_COMMAND'


@pytest.mark.parametrize('response',['bad','{"commands":[{"op":11}]}','{"commands":[{"op":2,"shell":1}]}','{"commands":[{"op":true}]}'])
def test_malformed_model_output_falls_back(response):
    hq=LocalHQ(transport=lambda _:response)
    assert hq.observe_and_issue(Engine(create_match()).observe(0))
    assert hq.last_decision['source']=='rules'


def test_timeout_and_remote_endpoint_rejected():
    def timeout(_):raise TimeoutError()
    hq=LocalHQ(transport=timeout);hq.observe_and_issue(Engine(create_match()).observe(0))
    assert hq.last_decision['source']=='rules'
    with pytest.raises(ValueError):LocalHQ('https://api.example.com/v1')


def test_real_http_protocol_loopback():
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    from threading import Thread
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            assert self.path=='/v1/chat/completions'
            assert payload['temperature']==0
            body=json.dumps({'choices':[{'message':{'content':'{"commands":[]}'}}]}).encode()
            self.send_response(200);self.end_headers();self.wfile.write(body)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        hq=LocalHQ(f'http://127.0.0.1:{server.server_port}/v1')
        assert hq.observe_and_issue(Engine(create_match()).observe(0))==[]
        assert hq.last_decision['source']=='llm'
    finally:server.shutdown();server.server_close();thread.join()
