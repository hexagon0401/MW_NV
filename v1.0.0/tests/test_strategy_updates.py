from collections import Counter
from copy import deepcopy
import numpy as np
import torch
from learning.decision_inputs import encode, REVISION
from learning.mission_env import MissionEnv, MissionTeacher
from learning.mission_initialize import initialize
from learning.league_policy import choose, update


def samples(n=96):
    mask=np.zeros(65,bool);mask[[0,64]]=True
    return [(np.zeros(1600,np.float32),mask.copy(),0,i%2,dict(mode=('conquest','elimination','capture_flag')[i%3],stage=('supply','transport')[i%2],input_revision=REVISION)) for i in range(n)]


def test_actual_update_calls_balanced_sampler():
    torch.set_num_threads(1);model=initialize(1);b=MissionTeacher();b.rows.extend(samples())
    x=np.zeros(1600,np.float32);mask=b.rows[0][1];a,v,lp=choose(model,x,mask)
    result=update(model,[dict(obs=x,mask=mask,action=a,value=v,logp=lp,reward=.1,start=True,terminal=True,advance=True)],0,b)
    assert b.stats['last_sample_counts']['mode']=={'elimination':13,'capture_flag':13,'conquest':6}
    assert sum(b.stats['last_sample_teams'].values())==32
    assert model.target_kl==.02 and 'approx_kl' in result['diagnostics']


def test_rejected_imitation_restores_weights_and_optimizer(monkeypatch):
    torch.set_num_threads(1);model=initialize(3);b=MissionTeacher();b.rows.extend(samples())
    before=deepcopy(model.policy.state_dict());optimizer=deepcopy(model.policy.optimizer.state_dict())
    def corrupt():
        with torch.no_grad():next(model.policy.parameters()).fill_(float('nan'))
    monkeypatch.setattr(model.policy.optimizer,'step',corrupt)
    # Nonfinite logits may raise while constructing the post-update distribution.
    assert b.imitate(model) is None
    assert all(torch.equal(v,model.policy.state_dict()[k]) for k,v in before.items())
    assert model.policy.optimizer.state_dict()==optimizer
    assert b.stats['imitation_rollbacks']==1


def test_mission_prefix_matches_rollout_and_preserves_training_history():
    e=MissionEnv();e.reset(7);obs=e.raw('A');items=e.items['A'];selected=items[:1]
    from agents.tactics import compatible
    e.selected['A']=selected;available=compatible(items,selected)
    a=e.vector('A');b=encode(obs,available,selected,mission=True)
    np.testing.assert_array_equal(a,b)
    obs['recent_summary']=[.9]*14
    np.testing.assert_allclose(encode(obs,available,selected,mission=True)[48:62],[.9]*14)
    assert b[17]==sum(c.get('supply_cost',0) for c in selected)/max(1,obs['resources']['supply'])


def test_legacy_teacher_labels_quarantined_without_changing_original(tmp_path):
    b=MissionTeacher();b.rows.extend(samples(2));row=b.rows[0];b.rows.append((*row[:4],{}))
    p=tmp_path/'teacher.npz';b.save(p);original=p.read_bytes();loaded=MissionTeacher();loaded.load(p)
    assert len(loaded.rows)==2 and loaded.stats['excluded_legacy_inputs']==1
    assert p.read_bytes()==original
