import json,sqlite3,time
from pathlib import Path
from server.dashboard_data import ingest,sample,files,reduce_points
from learning.results import insert,record_training

def match(id,at,kind='training',winner=0):return dict(kind='match',id=id,ended=True,mode=kind,rules_version='combined-arms-4',policies={'A':'a','B':'b'},scores=[100,40],winner=winner,seed=1,created_at=at,scenario_id='2',league=dict(run='run1',assignments={'A':'PPO2','B':'PPO1'}))
def test_incremental_idempotence_scope_and_team_learner_distinction(tmp_path):
    db=tmp_path/'results.sqlite';now=time.time();at=__import__('datetime').datetime.fromtimestamp(now,__import__('datetime').timezone.utc).isoformat()
    insert(db,match('one',at));assert ingest(db)==1 and ingest(db)==0
    snapshot=dict(training=dict(run_id='run1',rules_version='combined-arms-4'),resources={})
    output=files(db,snapshot,now);index=output['index.json'];v=output[index['views']['all:training:2:all']['document']]
    assert v['learning'][-1]['ppo1']==0 and v['learning'][-1]['ppo2']==100
    assert index['views']['all:training:2:PPO1']['total']==1
    other=files(db,dict(training=dict(run_id='other',rules_version='combined-arms-4')),now)
    assert not other[other['index.json']['views']['all:training:2:all']['document']]['learning']

def test_resource_retention_unknown_samples_and_bucket_ranges(tmp_path):
    db=tmp_path/'results.sqlite';now=10000000
    sample(db,dict(cpu_cores=None,memory_used_mib=100),at=now-8*86400)
    sample(db,dict(cpu_cores=0,memory_used_mib=120),at=now)
    sample(db,dict(cpu_cores=100),at=now)  # same sample cannot duplicate an hourly aggregate
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT count(*) FROM dash_samples').fetchone()[0]==1
        hours=[json.loads(r[0]) for r in conn.execute('SELECT payload FROM dash_hours')]
        assert sum(h.get('cpu_cores',{}).get('n',0) for h in hours)==1
    reduced=reduce_points([dict(at=i,label=str(i),cpu_cores=i%5) for i in range(1000)])
    assert len(reduced)==240 and max(p['cpu_cores_max'] for p in reduced)==4

def test_training_timestamp_is_not_fabricated_on_retry(tmp_path):
    db=tmp_path/'results.sqlite';assert record_training(db,'p',3,run_id='u1')
    with sqlite3.connect(db) as conn:first=conn.execute('SELECT payload FROM records').fetchone()[0]
    assert not record_training(db,'p',3,run_id='u1')
    with sqlite3.connect(db) as conn:assert conn.execute('SELECT payload FROM records').fetchone()[0]==first
    import pytest
    with pytest.raises(ValueError):record_training(db,'p',4,run_id='u1')
