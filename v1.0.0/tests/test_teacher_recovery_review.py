import json
from collections import deque
from types import SimpleNamespace
from learning.mission_coach import MissionCoach
from learning.mission_env import MissionTeacher
from learning.demonstrations import record_outcomes
import numpy as np


def test_checkpoint_cursor_rewinds_and_reimports_completed_labels_once(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);root=tmp_path/'run';coach=MissionCoach(root);coach.schedule(10)
    folder=coach.root/coach.state['jobs'][0];b=MissionTeacher()
    for team in (0,1):b.rows.append((np.zeros(1600),np.ones(65,dtype=bool),64,team,dict(tick=10,prefix=0)))
    b.save(folder/'samples.npz');coach.state['imported'][folder.name]=[10,1,0];coach.state['jobs']=[];coach._save()
    saved=root/'checkpoints/c/coaching';saved.mkdir(parents=True);(saved/'state.json').write_text('{"imported":{}}');(root/'current.json').write_text('{"path":"checkpoints/c"}')
    restored=MissionCoach(root);buffers=[MissionTeacher(),MissionTeacher()]
    restored.poll(buffers,[],paused=True);assert [len(b.rows) for b in buffers]==[1,1]
    restored.poll(buffers,[],paused=True);assert [len(b.rows) for b in buffers]==[1,1]


def test_resumed_outcomes_accumulate_without_updating_old_labels():
    old=(None,None,None,None,dict(tick=0));current=(None,None,None,None,dict(tick=150))
    teacher=SimpleNamespace(rows=deque([old,current]));totals={}
    first=record_outcomes(teacher,[dict(event_kind='DISEMBARK_DONE')],150,totals)
    result=record_outcomes(teacher,[dict(event_kind='BUILDING_ENTERED')],150,totals,first)
    assert result==totals==dict(DISEMBARK_DONE=1,BUILDING_ENTERED=1)
    assert current[4]['outcome']==result and 'outcome' not in old[4]


def test_stale_worker_identity_never_signals_reused_pid(tmp_path,monkeypatch):
    coach=MissionCoach(tmp_path);coach.state['worker']=dict(pid=99999999,start=1,job='missing');coach._save()
    monkeypatch.setattr('learning.mission_coach.os.kill',lambda *args:(_ for _ in ()).throw(AssertionError('foreign signal')))
    restored=MissionCoach(tmp_path);assert 'worker' not in restored.state


def test_recovered_finished_job_is_not_restarted(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);coach=MissionCoach(tmp_path/'run');coach.schedule(10)
    folder=coach.root/coach.state['jobs'][0];(folder/'slice.json').write_text('{"ended":true}')
    restored=MissionCoach(tmp_path/'run');restored.poll([MissionTeacher(),MissionTeacher()],[],paused=True)
    assert restored.state['jobs']==[] and restored.state['completed']==1


def test_terminal_resume_records_outcomes_without_querying_nim(tmp_path,monkeypatch):
    import gzip
    import learning.demonstrations as demo
    from engine.multi_scenario import create
    from engine.replay import encode
    monkeypatch.chdir(tmp_path);folder=tmp_path/'job';folder.mkdir()
    (folder/'job.json').write_text(json.dumps(dict(id='resume',run_id='fixture',scenario_id='3',seed=0,swap=False,kind='demonstration')))
    w=create(0,scenario_id='3');w.tick=149;w.scenario['time_limit_s']=30
    (folder/'world.json.gz').write_bytes(gzip.compress(json.dumps(encode(w)).encode()))
    (folder/'progress.json').write_text(json.dumps(dict(decision_tick=0,last_outcome=dict(DISEMBARK_DONE=1),stage_events=dict(DISEMBARK_DONE=1))))
    b=MissionTeacher();b.rows.append((np.zeros(1600),np.ones(65,dtype=bool),64,0,dict(tick=0,prefix=0)));b.save(folder/'samples.npz')
    original=demo.Engine.step
    def step(engine,dt):
        value=original(engine,dt);engine.world.emit('UNIT_RESUPPLIED',unit=1,ammo=30);return value
    monkeypatch.setattr(demo.Engine,'step',step)
    monkeypatch.setattr(demo.MissionTeacher,'collect',lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError('NIM after game end')))
    result=demo.run(folder,10,clients=[object(),object()],budget_root=tmp_path/'budget')
    assert result.ended and result.tick==150
    restored=MissionTeacher();restored.load(folder/'samples.npz')
    assert restored.rows[0][4]['outcome']==dict(DISEMBARK_DONE=1,UNIT_RESUPPLIED=1)
    assert json.loads((folder/'progress.json').read_text())['stage_events']==dict(DISEMBARK_DONE=1,UNIT_RESUPPLIED=1)
