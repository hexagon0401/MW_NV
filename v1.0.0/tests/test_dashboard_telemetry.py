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


def test_restored_stale_training_file_does_not_claim_a_dead_evaluation_is_running(tmp_path,monkeypatch):
    from server.telemetry import atomic
    monkeypatch.chdir(tmp_path);(tmp_path/'data/control').mkdir(parents=True)
    atomic(tmp_path/'data/training-status.json',dict(run_id='restored',status='running',phase='evaluation',workers=2,sim_speed=.5,games=200))
    atomic(tmp_path/'data/control/run.json',dict(run_id='restored',pid=99999999,process_start=1))
    result=training()
    assert result['status']=='offline' and result['phase']=='offline' and result['workers']==0
    assert result['sim_speed'] is None and result['games']==200 and result['last_recorded_phase']=='evaluation'


def test_missing_validation_pid_field_does_not_break_resource_collection(tmp_path,monkeypatch):
    from server.dashboard_service import pids
    monkeypatch.chdir(tmp_path);folder=tmp_path/'data/mission-normalization-v2';folder.mkdir(parents=True)
    (folder/'validation-agent.json').write_text('{}')
    assert pids()==set()
