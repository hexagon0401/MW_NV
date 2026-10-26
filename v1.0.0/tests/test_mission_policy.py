import numpy as np
import torch
from learning.mission_env import MissionEnv,MissionTeacher
from learning.mission_initialize import initialize
from learning.mission_policy import export,NumpyPolicy
from learning.league_policy import choose,update
from agents.mission_tactics import candidates


def test_equivariant_numpy_independent_critic_and_update(tmp_path):
    torch.set_num_threads(1);e=MissionEnv(scenario_id='4');e.reset(8);m=initialize(42);x=e.vector('A');mask=e.mask('A');p=tmp_path/'policy.npz';export(m,p);rng=torch.get_rng_state().clone();numpy=NumpyPolicy(p);assert torch.equal(rng,torch.get_rng_state())
    with torch.no_grad():logits=m.policy.mlp_extractor.forward_actor(torch.tensor(x[None]))[0].numpy()
    assert np.allclose(logits,numpy.logits(x),atol=2e-6)
    perm=np.random.default_rng(2).permutation(64);y=x.copy();y[64:]=x[64:].reshape(64,24)[perm].ravel()
    assert np.allclose(numpy.logits(y)[:64],logits[:64][perm],atol=2e-6)
    assert np.isclose(numpy.logits(y)[64],logits[64],atol=2e-6)
    net=m.policy.mlp_extractor;net.forward_actor(torch.tensor(x[None])).sum().backward();assert all(p.grad is None for n,p in net.named_parameters() if n.startswith('vf_'))
    rows=[]
    for i in range(4):
        a,v,lp=choose(m,x,mask);rows.append(dict(obs=x,mask=mask,action=a,value=v,logp=lp,reward=.1,terminal=i==3,start=i==0,advance=i==3))
    assert update(m,rows,0,MissionTeacher())['steps']==4
    m.save(tmp_path/'m');from sb3_contrib import MaskablePPO
    restored=MaskablePPO.load(tmp_path/'m');assert choose(m,x,mask,deterministic=True)[0]==choose(restored,x,mask,deterministic=True)[0]


def test_modes_and_no_time_shaping():
    for mode in ('2','3','4'):
        e=MissionEnv(scenario_id=mode);e.reset(2);assert e.vector('A').shape==(1600,);assert np.isfinite(e.vector('B')).all()
        before=e.engine.world.tick;result=e.step({'A':e.heuristic('A'),'B':e.heuristic('B')});assert e.engine.world.tick==before;assert result[1]=={'A':0.,'B':0.}


def test_teacher_contract_and_mission_anonymity(tmp_path):
    from agents.teacher import canonical_offer
    from agents.tactics import shortlist
    e=MissionEnv(scenario_id='4');e.reset(1);buffer=MissionTeacher();buffer.rows.append((e.vector('A'),e.mask('A'),64,0));buffer.save(tmp_path/'t.npz');restored=MissionTeacher();restored.load(tmp_path/'t.npz');assert restored.rows[0][0].shape==(1600,)
    payload,_=canonical_offer(e.raw('A'),shortlist(e.items['A']));assert payload['mission']['mode']=='capture_flag';assert {f['owner'] for f in payload['mission']['flags']}=={'SELF','OPPONENT'}
