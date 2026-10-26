import json,os,time
from server.telemetry import Activity,activities,Resources,atomic
from server.dashboard_data import files
from server.dashboard_service import training

def test_activity_lifecycle_dead_process_and_public_fields(tmp_path,monkeypatch):
    monkeypatch.setenv('MW_NV_ACTIVITY_ROOT',str(tmp_path))
    item=Activity('training','m1',run_id='r1',learners=['PPO1','PPO2']);item.update(10,force=True)
    rows=activities(tmp_path);assert len(rows)==1 and rows[0]['sim_seconds']==2
    assert not {'pid','process_start','path'}&set(rows[0])
    item.update(state='PAUSED',force=True);assert activities(tmp_path)[0]['state']=='PAUSED'
    item.close();assert activities(tmp_path)==[]
    atomic(tmp_path/'dead.json',dict(item.doc,pid=999999999,state='RUNNING',updated_at=time.time()));assert activities(tmp_path)==[]

def test_stale_collector_time_is_not_replaced_by_publication(tmp_path):
    snapshot=dict(updated_at='2000-01-01T00:00:00+00:00',training={},resources={})
    docs=files(tmp_path/'stats.sqlite',snapshot)
    assert docs['latest.json']['updated_at']==snapshot['updated_at']
    assert docs['resources-all.json']['updated_at']==snapshot['updated_at']

def test_control_observation_version_is_exported_without_private_fields(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);(tmp_path/'data').mkdir()
    atomic(tmp_path/'data/training-status.json',dict(run_id='r1',control_version=2,phase='paused',secret='never publish'))
    d=training();assert d['control_version']==2 and 'secret' not in d

def test_resource_usage_is_measured_not_fabricated():
    meter=Resources();first=meter.sample([os.getpid()]);assert first['cpu_cores'] is None
    second=meter.sample([os.getpid()]);assert second['cpu_cores'] is None or second['cpu_cores']>=0
    assert second['cpu_budget'] is None or 0<second['cpu_budget']<=4
