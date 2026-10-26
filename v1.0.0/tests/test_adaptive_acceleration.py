import gzip,json
from pathlib import Path
import numpy as np
import pytest
from learning.adaptive_resources import Adaptive
from learning.process_env import ProcessEnv,make_env,snapshot,restore
from learning.league_policy import advantages

def test_adaptive_quota_pressure_and_no_gain():
    r=dict(cpu_budget=4,memory_free_fraction=.8,cpu_pressure=0)
    a=Adaptive(now=0);a.observe(600,r,now=60);a.observe(600,r,now=120)
    assert a.workers==2 and a.trial
    a.observe(300,r,now=150);a.observe(300,r,now=180)
    assert a.workers==1 and a.reason=='trial_no_gain'
    a.workers=3;a.observe(1,dict(r,cpu_budget=2),now=181);assert a.workers==1
    a.workers=3;a.observe(1,dict(r,cpu_pressure=20),now=200);a.observe(1,dict(r,cpu_pressure=20),now=231)
    assert a.workers==2 and a.reason=='resource_pressure'

def test_process_step_and_snapshot_hash_matches_local():
    env=make_env('legacy');env.reset(19)
    worker=ProcessEnv('legacy')
    try:
        worker.call('load',dict(environment=snapshot(env),info=dict(active=True,metrics={'A':{'opportunities':{},'selected':{},'commands':[]},'B':{'opportunities':{},'selected':{},'commands':[]}},policy_spans={},assignments={})))
        for _ in range(2):
            env.step({'A':64,'B':64});p=worker.call('step',({'A':64,'B':64},0))
        b=worker.call('snapshot');assert b['environment']['world'].checksum()==env.engine.world.checksum()
        restored=restore(make_env('legacy'),b['environment']);restored.engine.step(1);env.engine.step(1)
        assert restored.engine.world.checksum()==env.engine.world.checksum()
    finally:worker.close()

def source(tmp_path):
    from learning.candidate_train import TrainingEnv
    from learning.candidate_policy import export
    from sb3_contrib import MaskablePPO
    m=MaskablePPO('MlpPolicy',TrainingEnv(stats=None),n_steps=64,batch_size=32,n_epochs=2,policy_kwargs={'net_arch':{'pi':[128,128],'vf':[128,128]}},device='cpu');p=tmp_path/'source.npz';export(m,p);return p

def test_two_process_ppo_update_checkpoint_and_resume(tmp_path,monkeypatch):
    import torch
    torch.set_num_threads(1)
    from learning.accelerated_league import run
    from learning.league_state import load
    from learning.teacher import TeacherBuffer
    from engine.replay import decode
    actor=source(tmp_path);monkeypatch.chdir(tmp_path);(tmp_path/'data').mkdir();monkeypatch.delenv('MW_NV_PUBLISH_TRAINING',raising=False)
    root=tmp_path/'run'
    state=run(root,actor,max_updates=1,teacher_enabled=False,fixed_workers=2,collection_rounds=4)
    assert state['generation']==1 and state['rounds']==4 and state['next_episode']==2
    assert state['runtime_schema']=='adaptive-1'
    for i in (1,2):assert state[f'ppo{i}_last_update']['steps']>0
    folder=root/json.loads((root/'current.json').read_text())['path']
    with gzip.open(folder/'environments.json.gz','rt') as f:bundles=decode(json.load(f))
    assert len(bundles)==2 and sum(b['environment']['world'].tick for b in bundles)==200
    # Resume with fewer execution slots: the second live game stays checkpointed.
    state=run(root,actor,max_updates=1,teacher_enabled=False,fixed_workers=1,collection_rounds=2)
    assert state['generation']==2 and state['rounds']==6 and state['next_episode']==2
    folder=root/json.loads((root/'current.json').read_text())['path']
    with gzip.open(folder/'environments.json.gz','rt') as f:after=decode(json.load(f))
    assert after[1]['environment']['world'].checksum()==bundles[1]['environment']['world'].checksum()
    from learning.league_archive import spool,verify,restore_bundle
    import hashlib
    archive=spool(root,folder,state,True);digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    assert verify(archive,digest,True)
    recovered=restore_bundle(archive,tmp_path/'recovered',digest)
    assert (recovered/'checkpoints/restored/environments.json.gz').exists()
    resumed=run(recovered,actor,max_updates=1,teacher_enabled=False,fixed_workers=1,collection_rounds=1)
    assert resumed['generation']==3 and resumed['next_episode']==2


def test_gae_bootstraps_each_environment_before_flatten(monkeypatch):
    import learning.accelerated_league as module
    monkeypatch.setattr(module,'choose',lambda model,x,*args,**kw:(64,float(x),0))
    def row():return dict(value=0,reward=0,terminal=False,advance=True)
    paths={(0,0,'A'):[row()],(1,1,'A'):[row()]}
    packets={0:dict(vectors={'A':2},masks={'A':None}),1:dict(vectors={'A':20},masks={'A':None})}
    rows=module.trajectory_rows(None,paths,packets)
    assert rows[0]['advantage']==pytest.approx(.99**(1/3)*2)
    assert rows[1]['advantage']==pytest.approx(.99**(1/3)*20)

def test_mission_parallel_uses_same_two_conditioned_policies(tmp_path,monkeypatch):
    import torch
    from learning.mission_initialize import initialize
    from learning.mission_policy import export
    from learning.accelerated_league import run
    torch.set_num_threads(1);source_dir=tmp_path/'actors';source_dir.mkdir()
    for i in (1,2):
        model=initialize(81+i);model.save(source_dir/f'ppo{i}.zip');export(model,source_dir/f'ppo{i}.npz')
    monkeypatch.chdir(tmp_path);(tmp_path/'data').mkdir();monkeypatch.delenv('MW_NV_PUBLISH_TRAINING',raising=False)
    state=run(tmp_path/'mission',source_dir,kind='mission',pilot=192,max_updates=1,teacher_enabled=False,fixed_workers=2,collection_rounds=2)
    assert state['contract']=='tactics-3' and state['next_episode']==2 and state['rounds']==2
    assert all(state[f'ppo{i}_last_update']['steps']>0 for i in (1,2))

def test_production_mission_requires_matching_t11_fingerprint(tmp_path):
    from learning.accelerated_league import run
    (tmp_path/'validation-gates.json').write_text(json.dumps(dict(approved_for_pilot=True,code_sha256='old-code')))
    with pytest.raises(ValueError,match='different code'):run(tmp_path,'unused',kind='mission')

def test_disk_limit_is_a_durable_pause_not_unverified_cleanup(tmp_path,monkeypatch):
    import torch
    from learning.accelerated_league import run
    import learning.background_io as publication
    torch.set_num_threads(1);actor=source(tmp_path);monkeypatch.chdir(tmp_path);(tmp_path/'data').mkdir();monkeypatch.delenv('MW_NV_PUBLISH_TRAINING',raising=False)
    def full(_):raise RuntimeError('ARCHIVE_DISK_LIMIT')
    monkeypatch.setattr(publication,'disk_guard',full)
    state=run(tmp_path/'run',actor,max_updates=1,teacher_enabled=False)
    assert state['pause_reason']=='ARCHIVE_DISK_LIMIT' and state['generation']==0
    folder=tmp_path/'run'/json.loads((tmp_path/'run/current.json').read_text())['path']
    assert (folder/'ppo1.zip').exists() and (folder/'environments.json.gz').exists()
    status=json.loads((tmp_path/'run/training-status.json').read_text())
    assert status['status']=='stopped' and status['pause_reason']=='ARCHIVE_DISK_LIMIT'
