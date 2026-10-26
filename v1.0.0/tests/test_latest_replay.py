import json
import pytest
from learning import replay_sink

class Store:
    bucket='fixture'
    def __init__(self):self.objects={'index.json':b'[]'};self.corrupt=False;self.deleted=[]
    def _request(self,path,method='GET',body=None):
        key=path.split(self.bucket+'/',1)[-1] if self.bucket+'/' in path else ''
        if method=='PUT':self.objects[key]=body;return b''
        if method=='DELETE':
            self.deleted.extend(json.loads(body)['prefixes'])
            for k in json.loads(body)['prefixes']:self.objects.pop(k,None)
            return b''
        if key not in self.objects:raise FileNotFoundError(key)
        if self.corrupt and key.startswith('training-replays/'):return b'bad'
        return self.objects[key]

@pytest.fixture
def store(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);monkeypatch.setenv('SUPABASE_URL','https://fixture');monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY','fixture')
    s=Store();monkeypatch.setattr(replay_sink,'PrivateStorage',lambda *a:s)
    monkeypatch.setattr(replay_sink,'export_view',lambda engine,initial:dict(initial={},summary=dict(scores=[engine,0],winner=0,ended=True),rules_version='fixture'))
    return s

def test_verified_latest_and_failure_keeps_previous_pointer(store,monkeypatch):
    monkeypatch.setattr(replay_sink.time,'time',lambda:1000)
    assert replay_sink.publish_latest(1,None)
    prior=store.objects['index.json'];entry=json.loads(prior)[0]
    assert entry['sha256'] in entry['replay_uri']
    store.corrupt=True
    with pytest.raises(ValueError):replay_sink.publish_latest(2,None)
    assert store.objects['index.json']==prior
    assert not replay_sink.publish_latest(3,None,{'completed_at':999})

def test_retains_two_generations_and_ten_minute_grace(store,monkeypatch):
    now=[1000];monkeypatch.setattr(replay_sink.time,'time',lambda:now[0])
    for i in (1,2,3):replay_sink.publish_latest(i,None);now[0]+=1
    assert not store.deleted
    now[0]=1700;replay_sink.publish_latest(4,None)
    assert len(store.deleted)==2
    history=json.loads(store.objects['training-replay-retention.json'])
    assert len(history)==2 and json.loads(store.objects['index.json'])[0]['replay_uri'].endswith(history[-1]['key'])
