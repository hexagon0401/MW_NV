import json,types
import numpy as np
import pytest
from agents.local_hq import LocalHQ
from agents.teacher import canonical_offer
from agents.tactics import candidates,shortlist
from learning.candidate_env import CandidateEnv
from learning.teacher import TeacherBuffer,TeacherPPO
from learning.self_play import SelfPlayEnv,checkpoint,current

def clients(fail=False):
    a=LocalHQ(transport=lambda p:'{"candidate_ids":[0]}')
    def bad(p):raise TimeoutError()
    return [a,LocalHQ(transport=bad) if fail else a]

def test_teacher_pair_isolation_no_world_mutation_and_failure_symmetry():
    env=CandidateEnv();env.reset(0);before=env.engine.world.checksum();b=TeacherBuffer();b.collect(env,clients())
    assert b.stats['paired']==1 and {r[3] for r in b.rows}=={0,1}
    assert env.engine.world.checksum()==before
    failed=TeacherBuffer();failed.collect(env,clients(True));assert not failed.rows and failed.stats['skipped']==1
    obs=env.raw('A');payload,_=canonical_offer(obs,shortlist(candidates(obs)));text=json.dumps(payload)
    assert 'team' not in payload and 'SELF' in text and 'OPPONENT' in text
    assert all('unit' not in c and 'target' not in c for c in payload['candidates'])
    from engine.types import WorldPos
    hidden=env.engine.world.vehicles[20200];hidden.pos=WorldPos(hidden.pos.x_cm+100,hidden.pos.y_cm)
    assert canonical_offer(env.raw('A'),shortlist(candidates(env.raw('A'))))[0]==payload

def test_teacher_mask_and_imitation_actor_update(tmp_path):
    e=CandidateEnv();e.reset(0);b=TeacherBuffer()
    for _ in range(16):b.collect(e,clients())
    for x,mask,action,team in b.rows:assert mask[action] and x.shape==(1056,)
    from learning.candidate_train import TrainingEnv
    model=TeacherPPO('MlpPolicy',TrainingEnv(stats=None),n_steps=64,batch_size=32,policy_kwargs={'net_arch':{'pi':[128,128],'vf':[128,128]}},device='cpu')
    import torch
    before=model.policy.action_net.weight.detach().clone();value=model.policy.value_net.weight.detach().clone()
    assert b.imitate(model) is not None
    assert not torch.equal(before,model.policy.action_net.weight) and torch.equal(value,model.policy.value_net.weight)
    b.save(tmp_path/'teacher.npz');loaded=TeacherBuffer();loaded.load(tmp_path/'teacher.npz');assert len(loaded.rows)==len(b.rows)

def test_environment_checkpoint_and_role_side_balance(tmp_path):
    from learning.candidate_policy import export
    from learning.candidate_train import TrainingEnv
    model=TeacherPPO('MlpPolicy',TrainingEnv(stats=None),n_steps=64,batch_size=32,policy_kwargs={'net_arch':{'pi':[128,128],'vf':[128,128]}},device='cpu')
    export(model,tmp_path/'champion.npz');(tmp_path/'opponents').mkdir();b=TeacherBuffer();env=SelfPlayEnv(tmp_path,b);env.parallel.teacher_hook=lambda e:None
    roles=[]
    for _ in range(4):
        env.reset();hq=next(f for f in env.parallel.engine.world.facilities.values() if f.kind=='HQ' and int(f.owner)==('A','B').index(env.controlled));roles.append((env.controlled,hq.pos.x_cm))
    assert len(set(roles))==4
    snapshot=env.snapshot();other=SelfPlayEnv(tmp_path,b);other.restore(snapshot)
    assert other.parallel.engine.world.checksum()==env.parallel.engine.world.checksum()
    assert np.array_equal(other.parallel.vector(other.controlled),env.parallel.vector(env.controlled))
    checkpoint(tmp_path,model,env,b,dict(generation=1,completed_games=0));assert (current(tmp_path)/'latest.zip').is_file()
    from learning.backup import pack,restore
    archive,digest=pack(tmp_path,1);dest=tmp_path/'restore';restore(archive,dest,digest);assert (dest/'environment.json').is_file()
    with pytest.raises(ValueError):restore(archive,dest,'bad')

def test_completed_record_idempotent(tmp_path):
    from engine.runtime import Engine
    from engine.scenario import create_release_match
    from learning.results import record_world,aggregate
    w=Engine(create_release_match()).world;w.ended=True;w.winner=0
    db=tmp_path/'results.sqlite';assert record_world(db,w,'training',{'A':'p','B':'q'},match_id='same')
    assert not record_world(db,w,'training',{'A':'p','B':'q'},match_id='same')
    assert aggregate(db)['total_matches']==1

def test_backup_threshold_and_failure_preserves_prior(tmp_path,monkeypatch):
    from learning.self_play import backup_due
    from learning import backup
    assert not backup_due(9,0) and backup_due(10,0) and not backup_due(10,10)
    assert backup_due(20,10)
    (tmp_path/'latest.zip').write_bytes(b'fixture');(tmp_path/'state.json').write_text('{"completed_games":10}')
    (tmp_path/'backup-status.json').write_text('verified-old')
    def fail(*args,**kwargs):raise RuntimeError('network unavailable')
    monkeypatch.setattr(backup,'gh',fail)
    with pytest.raises(RuntimeError):backup.publish(tmp_path,1)
    assert (tmp_path/'backup-status.json').read_text()=='verified-old'
    assert len(list((tmp_path/'backups').glob('*.gz')))==1

def test_retry_after_skips_both_teams():
    from urllib.error import HTTPError
    def limited(p):raise HTTPError('https://fixture',429,'rate limited',{'Retry-After':'120'},None)
    c=LocalHQ(transport=limited);e=CandidateEnv();e.reset(0);b=TeacherBuffer();b.collect(e,[c,c]);assert not b.rows
    requests=b.stats['requests'];b.collect(e,[c,c]);assert b.stats['requests']==requests and b.stats['skipped']==2
