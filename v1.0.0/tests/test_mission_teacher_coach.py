import json
import numpy as np
from learning.mission_env import MissionTeacher
from learning.nim_budget import PairLease
from learning.mission_coach import MissionCoach

def row(i,mode,stage='supply'):
    return (np.full(1600,i,dtype=np.float32),np.ones(65,dtype=bool),64,i%2,dict(mode=mode,stage=stage,tick=i,prefix=0))

def test_mode_and_stage_balancing_unique_and_restore(tmp_path):
    b=MissionTeacher()
    for i in range(100):b.rows.append(row(i,'elimination' if i<40 else 'capture_flag' if i<80 else 'conquest',str(i%3)))
    selected=b.sample_rows();assert len(selected)==32 and len({r[4]['tick'] for r in selected})==32
    assert [sum(r[4]['mode']==m for r in selected) for m in ('elimination','capture_flag','conquest')]==[13,13,6]
    b.save(tmp_path/'buffer.npz');r=MissionTeacher();r.load(tmp_path/'buffer.npz');assert r.rows[-1][4]==b.rows[-1][4]

def test_pair_rate_concurrency_priority_and_restart(tmp_path,monkeypatch):
    clock=[100.];monkeypatch.setattr('learning.nim_budget.time.time',lambda:clock[0])
    pending=tmp_path/'demonstration-pending';pending.touch()
    # No pending lane: ordinary may use the budget, but another process cannot overlap.
    pending.unlink()
    with PairLease(tmp_path) as admitted:
        assert admitted
        with PairLease(tmp_path) as second:assert not second
    with PairLease(tmp_path) as admitted:assert not admitted
    clock[0]+=30
    lease=PairLease(tmp_path)
    with lease as admitted:assert admitted;lease.defer(120)
    clock[0]+=31
    with PairLease(tmp_path,'demonstration') as admitted:assert not admitted

def test_coach_schedule_does_not_change_training_counters(tmp_path):
    c=MissionCoach(tmp_path);c.schedule(29);assert len(c.state['jobs'])==2 and c.state['scheduled']==2
    modes=[json.loads((c.root/j/'job.json').read_text())['scenario_id'] for j in c.state['jobs']]
    assert modes==['3','4'];c.schedule(29);assert len(c.state['jobs'])==2
    r=MissionCoach(tmp_path);assert r.state['jobs']==c.state['jobs']

def test_demo_executes_separately_and_keeps_original_labels(tmp_path,monkeypatch):
    import learning.demonstrations as demo
    from engine.multi_scenario import create
    monkeypatch.chdir(tmp_path)
    def short(seed,swap=False,scenario_id='3'):
        w=create(seed,swap,scenario_id);w.scenario['time_limit_s']=.6;return w
    monkeypatch.setattr(demo,'create',short)
    monkeypatch.setattr('learning.teacher.choose',lambda client,obs,items:items[:1])
    folder=tmp_path/'job';folder.mkdir();(folder/'job.json').write_text(json.dumps(dict(id='fixture',run_id='isolated',scenario_id='3',seed=0,swap=False,kind='demonstration')))
    w=demo.run(folder,cpu_seconds=10,clients=[object(),object()],budget_root=tmp_path/'budget')
    assert w.ended and w.tick==3
    b=MissionTeacher();b.load(folder/'samples.npz');assert b.rows and all(r[4]['source']=='demonstration' for r in b.rows)
    from learning.results import records,aggregate
    assert records('data/results.sqlite')[0]['mode']=='demonstration'
    assert aggregate('data/results.sqlite')['total_matches']==0


def test_demo_side_and_start_balance_per_mode(tmp_path):
    c=MissionCoach(tmp_path);c.schedule(80)
    jobs=[json.loads((c.root/j/'job.json').read_text()) for j in c.state['jobs']]
    for mode in ('3','4'):
        assert {(j['swap'],j['swap_learners']) for j in jobs if j['scenario_id']==mode}=={(False,False),(False,True),(True,False),(True,True)}

def test_comparison_training_isolates_status_control_and_ledger(tmp_path,monkeypatch):
    import learning.teacher_comparison as experiment
    seen=[]
    class Done(Exception):pass
    def call(args,**kw):seen.append(kw);raise Done()
    monkeypatch.setattr(experiment.subprocess,'run',call)
    import pytest
    with pytest.raises(Done):experiment.run(tmp_path/'study',tmp_path/'models',1)
    call=seen[0];assert call['cwd']==(tmp_path/'study/baseline').resolve()
    assert call['env']['MW_NV_CONTROL_ROOT']==str((tmp_path/'study/baseline/control').resolve())
    assert call['env']['MW_NV_PUBLISH_TRAINING']=='0'
