import gzip,json,time,random
from pathlib import Path
from engine.replay import encode,decode
from learning.checkpoint_io import write_environment
from learning.training_status import Reporter

def test_fast_writer_preserves_complete_payload_and_rng(tmp_path):
    data={'events':[{'tick':i,'kind':'UNIT_MOVED','x':i*2} for i in range(1000)],'rng':random.Random(52),'tuple':(1,2)}
    prior=data['rng'].getstate();path=tmp_path/'env.gz';write_environment(path,data)
    with gzip.open(path,'rt') as f:stored=json.load(f)
    assert stored==json.loads(json.dumps(encode(data)))
    restored=decode(stored);assert restored['events']==data['events'] and restored['rng'].getstate()==prior
    assert data['rng'].getstate()==prior

def test_busy_heartbeat_survives_slow_save_and_exception(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);Path('data').mkdir();root=Path('run');root.mkdir();r=Reporter(root,1);r(dict(phase='learning',sim_seconds=10),force=True)
    import pytest
    with pytest.raises(RuntimeError):
        with r.busy(interval=.02):
            first=json.loads((root/'training-status.json').read_text());time.sleep(.07);second=json.loads((root/'training-status.json').read_text())
            assert second['phase']=='checkpoint' and second['sim_speed'] is None
            assert second['updated_at']>first['updated_at'] and second['sim_seconds']==10
            raise RuntimeError('failed save')
    last=json.loads((root/'training-status.json').read_text());assert last['phase']=='learning' and last['checkpoint_seconds']>=.06
    assert not any(t.name=='checkpoint-heartbeat' for t in __import__('threading').enumerate())


def test_metadata_commit_never_rewrites_environment_or_rng(tmp_path):
    from learning.checkpoint_io import commit_metadata
    folder=tmp_path/'checkpoints'/'one';folder.mkdir(parents=True)
    (tmp_path/'current.json').write_text(json.dumps({'path':'checkpoints/one'}))
    (folder/'state.json').write_text(json.dumps({'generation':4,'last_policy_archive':0}))
    for name in ('environment.json.gz','rng.json','ppo1.zip'):(folder/name).write_bytes(b'unchanged')
    before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in folder.iterdir() if p.name!='state.json'}
    commit_metadata(tmp_path,{'generation':4,'last_policy_archive':10})
    assert json.loads((folder/'state.json').read_text())['last_policy_archive']==10
    assert before=={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in folder.iterdir() if p.name!='state.json'}
