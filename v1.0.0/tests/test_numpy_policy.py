import numpy as np
import torch
from sb3_contrib import MaskablePPO
from learning.train import TrainingEnv
from learning.policies import NumpyPolicy,export_numpy


def test_portable_logits_match_torch_for_masked_actions(tmp_path):
    torch.set_num_threads(1)
    model=MaskablePPO('MlpPolicy',TrainingEnv(),n_steps=64,batch_size=32,policy_kwargs={'net_arch':{'pi':[32,32],'vf':[32,32]}},seed=2)
    path=tmp_path/'model.npz';export_numpy(model,path);policy=NumpyPolicy(path)
    rng=np.random.default_rng(7)
    for _ in range(100):
        obs=rng.random(32,dtype=np.float32);mask=rng.random(20)>.5;mask[0]=True
        action,_=model.predict(obs,deterministic=True,action_masks=mask)
        assert int(action)==policy.predict(obs,mask)
