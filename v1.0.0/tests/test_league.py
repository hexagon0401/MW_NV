from collections import Counter
from pathlib import Path
import json
import numpy as np
import pytest
import torch
from learning.league_policy import schedule,initialize,choose,advantages,update
from learning.teacher import TeacherBuffer
from learning.candidate_env import CandidateEnv
from learning.league import assignments
from learning.league_state import save,load
from learning.candidate_policy import export,CandidatePolicy

@pytest.fixture
def source(tmp_path):
    # Construct an ordinary compatible actor for migration; no network/model download.
    from learning.candidate_train import TrainingEnv
    from sb3_contrib import MaskablePPO
    torch.set_num_threads(1)
    m=MaskablePPO('MlpPolicy',TrainingEnv(stats=None),n_steps=64,batch_size=32,n_epochs=2,policy_kwargs={'net_arch':{'pi':[128,128],'vf':[128,128]}},device='cpu');p=tmp_path/'source.npz';export(m,p);return p

def test_schedule_balances_learner_team_location_and_opponent():
    a=schedule(0);assert a==schedule(0) and a!=schedule(1)
    assert Counter(r['kind'] for r in a)=={'duel':16,'past':8,'algorithm':8}
    solo=Counter((r['kind'],r['learner'],r['team'],r['swap']) for r in a if r['kind']!='duel');assert set(solo.values())=={1}
    for row in a:
        assigned=assignments(row)
        if row['kind']=='duel':assert set(assigned.values())=={'PPO1','PPO2'}

def test_time_gae_ignores_intra_hq_selection_count():
    def row(reward=0,advance=False,terminal=False):return dict(value=0.,reward=reward,advance=advance,terminal=terminal)
    a=advantages([row(),row(1,True),row(2,True,True)])
    assert a[0]==a[1]
    assert a[1]==pytest.approx(1+(.99*.95)**(1/3)*2)
    b=advantages([row(1,True,True),row(100,True,True)]);assert b[0]==1

def test_independent_update_imitation_and_resume(tmp_path,source):
    models=[initialize(source,1),initialize(source,2)];buffers=[TeacherBuffer(),TeacherBuffer()];query=TeacherBuffer();env=CandidateEnv(decision_seconds=10);env.reset(0);g=[torch.Generator().manual_seed(5),torch.Generator().manual_seed(6)]
    obs=env.vector('A');mask=env.mask('A');before={k:v.clone() for k,v in models[1].policy.state_dict().items()};value_before=models[0].policy.value_net.weight.clone()
    rows=[]
    for n in range(32):
        a,v,lp=choose(models[0],obs,mask,g[0]);rows.append(dict(obs=obs,mask=mask,action=a,value=v,logp=lp,reward=float(n%2),terminal=n==31,advance=True,start=n==0))
    result=update(models[0],rows,0,buffers[0]);assert result['steps']==32
    assert all(torch.equal(v,models[1].policy.state_dict()[k]) for k,v in before.items())
    assert not torch.equal(value_before,models[0].policy.value_net.weight)
    from engine.version import RULES_VERSION,CATALOG_VERSION
    state=dict(run='test',generation=1,completed_games=0,rules_version=RULES_VERSION,catalog_version=CATALOG_VERSION,contract='tactics-2')
    save(tmp_path,models,env,buffers,query,g,state);expected=env.engine.world.checksum();rng=g[0].get_state().clone()
    restored_env=CandidateEnv(decision_seconds=10);restored_env.reset(3);restored,loaded=load(tmp_path,restored_env,[TeacherBuffer(),TeacherBuffer()],TeacherBuffer(),g)
    assert restored_env.engine.world.checksum()==expected and torch.equal(rng,g[0].get_state())
    for left,right in zip(models,restored):assert all(torch.equal(v,right.policy.state_dict()[k]) for k,v in left.policy.state_dict().items())
    for role in ('A','B'):assert np.array_equal(env.vector(role),restored_env.vector(role))

def test_teacher_only_at_30s_not_10_or_20():
    e=CandidateEnv(decision_seconds=10);e.reset(0);seen=[];e.teacher_hook=lambda env:seen.append(env.engine.world.tick)
    for _ in range(6):e.step({'A':64,'B':64})
    assert seen==[150,300]

def test_candidates_isolated_and_cooldown():
    from agents.tactics import candidates
    e=CandidateEnv();e.reset(0);obs=e.raw('A');items=candidates(obs);assert len(items)<=64
    assert any(c['analysis']['tactic'].startswith('flank') for c in items)
    chosen=next(c for c in items if c['role']=='capture');f=next(f for f in obs['facilities'] if f['id']==chosen['command']['target']);obs['failed_goals']=[dict(unit=chosen['command']['unit'],**f['pos'])]
    assert not any(c['command']==chosen['command'] for c in candidates(obs))

def test_real_coordinator_short_games_updates_both_and_resumes(tmp_path,source,monkeypatch):
    import learning.league as league
    import learning.league_evaluate as evaluation
    import learning.league_archive as archives
    from engine.scenario import create_match
    monkeypatch.chdir(tmp_path);(tmp_path/'data').mkdir();monkeypatch.delenv('MW_NV_PUBLISH_TRAINING',raising=False)
    def tiny(seed=0,swap=False):
        w=create_match(seed,swap);w.teams[0].score=100;return w
    monkeypatch.setattr(league,'training_scenario',tiny)
    monkeypatch.setattr(evaluation,'evaluate',lambda *a,**k:{'complete':True})
    monkeypatch.setattr(archives,'publish_pending',lambda *a:{'status':'deferred','failures':[{}]})
    state=league.run(tmp_path/'run',source,max_updates=1,teacher_enabled=False)
    assert state['generation']==1 and state['completed_games']==64
    assert state['ppo1_last_update']['steps']>0 and state['ppo2_last_update']['steps']>0
    resumed=league.run(tmp_path/'run',source,max_updates=1,teacher_enabled=False)
    assert resumed['generation']==2 and resumed['completed_games']==128
    from learning.results import records
    matches=records('data/results.sqlite','match');assert len(matches)==128
    assert all(r['league']['metrics']['teams'] for r in matches)
    current=tmp_path/'run'/json.loads((tmp_path/'run/current.json').read_text())['path']
    path=archives.spool(tmp_path/'run',current,resumed,full=True)
    digest=__import__('hashlib').sha256(path.read_bytes()).hexdigest();assert archives.verify(path,digest,True)
    with pytest.raises(ValueError):archives.verify(path,'wrong',True)
    restored=archives.restore_bundle(path,tmp_path/'recovered',digest)
    e=CandidateEnv(decision_seconds=10);e.reset(0);loaded_models,loaded_state=load(restored,e,[TeacherBuffer(),TeacherBuffer()],TeacherBuffer(),[torch.Generator(),torch.Generator()])
    assert loaded_state['generation']==2 and loaded_models[0].policy.optimizer.state
    with pytest.raises(ValueError,match='empty'):archives.restore_bundle(path,restored,digest)


def test_frozen_evaluation_is_crossed_and_resume_does_not_duplicate(tmp_path,source,monkeypatch):
    from learning.league_evaluate import evaluate
    from engine.scenario import create_match
    monkeypatch.chdir(tmp_path);(tmp_path/'data').mkdir();root=tmp_path/'eval';(root/'baseline').mkdir(parents=True)
    models=[initialize(source,3),initialize(source,4)]
    for i,m in enumerate(models):export(m,root/'baseline'/f'ppo{i+1}.npz')
    def tiny(seed=0,swap=False):
        w=create_match(seed,swap);w.teams[0].score=100;return w
    state=dict(run='fixture',completed_games=0,generation=0)
    before=[{k:v.clone() for k,v in m.policy.state_dict().items()} for m in models]
    result=evaluate(root,models,state,seeds=[10000],scenario_factory=tiny)
    assert result['complete'] and len(result['results'])==16
    assert len({(r['team'],r['swapped']) for r in result['results']})==4
    assert evaluate(root,models,state,seeds=[10000],scenario_factory=tiny)==result
    for i,m in enumerate(models):assert all(torch.equal(v,m.policy.state_dict()[k]) for k,v in before[i].items())

def test_maps_cross_role_schedule_over_four_blocks():
    groups={}
    for block in range(4):
        for row in schedule(block):groups.setdefault((row['kind'],row['learner'],row['team'],row['swap']),set()).add(row['family'])
    assert all(values=={0,1,2,3} for values in groups.values())
