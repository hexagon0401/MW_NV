"""Bounded CPU MaskablePPO against a frozen opponent; NumPy deployment export."""
from pathlib import Path
import gymnasium as gym
import numpy as np
import torch
from sb3_contrib import MaskablePPO
from .env import HQEnv
from .policies import choose,NumpyPolicy,export_numpy


class TrainingEnv(gym.Env):
    def __init__(self,controlled='A',opponent=None):
        self.parallel=HQEnv();self.controlled=controlled;self.other='B' if controlled=='A' else 'A'
        self.opponent=NumpyPolicy(opponent) if opponent else None;self.episode=0
        self.observation_space=self.parallel.observation_space(controlled);self.action_space=self.parallel.action_space(controlled)
    def reset(self,seed=None,options=None):
        super().reset(seed=seed)
        selected=self.episode%50 if seed is None else seed%50;self.episode+=1
        obs,info=self.parallel.reset(seed=selected);return obs[self.controlled],{}
    def action_masks(self):return self.parallel.mask(self.controlled)
    def step(self,action):
        e=self.parallel
        other=self.opponent.predict(e.vector(self.other),e.mask(self.other)) if self.opponent else choose(e,self.other)
        obs,rewards,done,trunc,infos=e.step({self.controlled:int(action),self.other:other})
        return obs[self.controlled],rewards[self.controlled],done[self.controlled],trunc[self.controlled],infos[self.controlled]


def train(output,steps=256,controlled='A',opponent=None,seed=0):
    torch.set_num_threads(2)
    env=TrainingEnv(controlled,opponent)
    model=MaskablePPO('MlpPolicy',env,n_steps=64,batch_size=32,n_epochs=2,policy_kwargs={'net_arch':{'pi':[32,32],'vf':[32,32]}},seed=seed,device='cpu',verbose=0)
    model.learn(total_timesteps=steps)
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
    model.save(str(path));export_numpy(model,path.with_suffix('.npz'))
    loaded=MaskablePPO.load(str(path),device='cpu');obs,_=env.reset(seed=7)
    action,_=model.predict(obs,deterministic=True,action_masks=env.action_masks())
    check,_=loaded.predict(obs,deterministic=True,action_masks=env.action_masks())
    assert action==check
    assert NumpyPolicy(path.with_suffix('.npz')).predict(obs,env.action_masks())==int(action)
    return model


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',default='data/policies/policy0');p.add_argument('--steps',type=int,default=256);args=p.parse_args()
    train(args.output,args.steps);print('CPU training, save/load and NumPy prediction parity: PASS')
