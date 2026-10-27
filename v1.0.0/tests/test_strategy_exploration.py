import numpy as np
import torch
from gymnasium.spaces import Box
from learning.exploration_env import ExplorationEnv
from learning.exploration_features import OBS_SIZE
from learning.mission_initialize import ShapeEnv
from learning.mission_policy import MissionPolicy,export
from learning.mission_numpy import NumpyPolicy
from learning.process_env import snapshot,restore
from agents.exploration_routes import route,balanced


def test_exploration_numpy_and_checkpoint_history(tmp_path):
    from sb3_contrib import MaskablePPO
    torch.set_num_threads(1)
    class Shape(ShapeEnv):observation_space=Box(-4,4,(OBS_SIZE,),np.float32)
    m=MaskablePPO(MissionPolicy,Shape(),n_steps=4,batch_size=4,device='cpu');p=tmp_path/'p.npz';export(m,p);npmodel=NumpyPolicy(p)
    e=ExplorationEnv();e.reset(3);x=e.vector('A');mask=e.mask('A')
    assert x.shape==(2112,) and npmodel.contract=='tactics-5'
    with torch.no_grad():actual=m.policy.mlp_extractor.forward_actor(torch.tensor(x[None]))[0].numpy()
    np.testing.assert_allclose(actual,npmodel.logits(x),atol=2e-6)
    before=e.engine.world.tick
    while e.engine.world.tick==before:e.step({a:64 for a in e.agents})
    assert len(e.summary_history['A'])==7
    payload=snapshot(e);other=restore(ExplorationEnv(),payload)
    np.testing.assert_array_equal(e.vector('A'),other.vector('A'))
    while e.engine.world.tick==other.engine.world.tick:
        e.step({a:64 for a in e.agents});break
    other.step({a:64 for a in other.agents})
    assert e.summary_history==other.summary_history and e.engine.world.checksum()==other.engine.world.checksum()


def test_routes_bounded_and_visibility_only():
    obs=dict(terrain=[[0]*30 for _ in range(30)],enemies=[],catalog=dict(units={'INF':{}},vehicles={}))
    actor=dict(type_id='INF',pos=dict(x_cm=200,y_cm=200))
    first=route(obs,actor,(10000,10000),'avoid')
    assert first and first[1]['risk']==0 and first[1]['unexplored'] is None
    obs['enemies']=[dict(pos=dict(x_cm=5000,y_cm=5000))]
    assert route(obs,actor,(10000,10000),'avoid')[1]['risk']>=0
    assert route(obs,actor,(10000,10000),'avoid',max_nodes=1) is None


def test_group_quotas_and_variation_determinism():
    from learning.scenario_variants import create
    a=create(4,scenario_id='2');b=create(4,scenario_id='2')
    assert a.checksum()==b.checksum()
    assert all(a.terrain.passable(u.pos.x_cm,u.pos.y_cm) for u in a.soldiers.values())
    assert .8<=a.training_variant['resource_multiplier']<=1.2
    items=[dict(role=role,score=i,command=dict(unit=i)) for role in ('flag','attack','transport','supply') for i in range(25)]
    result=balanced(items)
    assert len(result)==64 and all(sum(c['role']==r for c in result)==16 for r in ('flag','attack','transport','supply'))


def test_successor_preparation_rejects_unfinished_pilot(tmp_path):
    import json,pytest
    from learning.exploration_bootstrap import prepare
    (tmp_path/'state.json').write_text(json.dumps(dict(contract='tactics-4',completed_games=191)))
    (tmp_path/'validation-gates.json').write_text('{}')
    with pytest.raises(ValueError,match='pilot'):prepare(tmp_path,tmp_path/'next')
    assert not (tmp_path/'next').exists()


def test_distillation_only_matches_real_commands(tmp_path):
    from learning.mission_initialize import initialize
    from learning.exploration_bootstrap import distill
    torch.set_num_threads(1);m=initialize(5);source=tmp_path/'old.npz';export(m,source)
    report=distill(source,tmp_path/'new.zip',seed=6,rounds=1,epochs=1)
    assert report['matched_commands_only'] and report['critic_fresh'] and report['optimizer_fresh']
    assert NumpyPolicy(tmp_path/'new.npz').contract=='tactics-5'


def test_tank_routes_fit_sixteen_metre_corridor():
    cells=[[6]*30 for _ in range(20)]
    for row in cells[8:12]:row[:]=[1]*30
    obs=dict(terrain=cells,enemies=[],catalog=dict(units={},vehicles={'TANK':{'footprint_cm':[900,450]}}))
    actor=dict(type_id='TANK',pos=dict(x_cm=2000,y_cm=4000))
    assert route(obs,actor,(10000,4000),'shortest') is not None
