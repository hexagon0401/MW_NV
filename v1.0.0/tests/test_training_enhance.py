import json
import numpy as np
from learning.training_maps import training_scenario
from learning.candidate_env import CandidateEnv

def test_variants_deterministic_and_preserve_roster_and_passable_spawns():
    hashes=[]
    for seed in range(4):
        a=training_scenario(seed);b=training_scenario(seed)
        assert a.checksum()==b.checksum()
        assert len(a.soldiers)==128 and len(a.vehicles)==20
        assert all(a.terrain.passable(v.pos.x_cm,v.pos.y_cm,True) for v in a.vehicles.values())
        hashes.append(a.checksum())
    assert len(set(hashes))==4

def test_external_scenario_factory_and_fixed_observation():
    calls=[]
    def factory(seed,swap):calls.append((seed,swap));return training_scenario(seed,swap)
    e=CandidateEnv(scenario_factory=factory);obs,_=e.reset(3,options={'swap':True})
    assert calls==[(3,True)] and obs['A'].shape==(1056,) and np.isfinite(obs['A']).all()

def test_continued_optimizer_steps_and_numpy_parity(tmp_path):
    from learning.candidate_train import train
    a=tmp_path/'a';b=tmp_path/'b'
    first=train(a,64,stats=None);second=train(b,64,stats=None,resume=str(a.with_suffix('.zip')),seed=1)
    assert first.num_timesteps==64 and second.num_timesteps==128
    meta=json.loads(b.with_suffix('.json').read_text());assert meta['resumed_from']==str(a.with_suffix('.zip')) and meta['policy_steps']==128

def test_retention_keeps_latest_eight_and_milestones(tmp_path):
    from learning.continuous import prune_checkpoints
    for n in range(12):
        for suffix in ('.npz','.zip','.json'):(tmp_path/f'round-{n:06d}{suffix}').write_text('fixture')
    prune_checkpoints(tmp_path,11)
    assert sorted(p.stem for p in tmp_path.glob('*.npz'))==['round-000000']+[f'round-{i:06d}' for i in range(4,12)]
