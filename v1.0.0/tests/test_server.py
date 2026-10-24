import pytest
pytest.importorskip("fastapi")
pytest.importorskip("httpx")
import json
from pathlib import Path
from fastapi.testclient import TestClient
from server.app import create_app


def test_finished_match_endpoints_and_read_only(tmp_path):
    data=json.loads(Path('viewer/public/demo.json').read_text())
    (tmp_path/'demo.view.json').write_text(json.dumps(data))
    client=TestClient(create_app(tmp_path))
    assert client.get('/matches').json()[0]['id']=='demo'
    assert client.get('/matches/demo').json()['summary']['ended']
    assert client.get('/snapshot?match_id=demo').json()==data['final']
    assert len(client.get('/events?match_id=demo&limit=2').json())==2
    assert client.get('/matches/demo/view').json()['initial']==data['initial']
    assert client.post('/matches/demo').status_code==405
    assert client.get('/matches/unknown').status_code==404
    data['summary']['ended']=False
    (tmp_path/'hidden.view.json').write_text(json.dumps(data))
    assert client.get('/matches/hidden/view').status_code==404
