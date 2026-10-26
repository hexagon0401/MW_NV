"""Independent actor distillation across matched commands; fresh critic and optimizer."""
import hashlib,json
from pathlib import Path
import gymnasium as gym
from gymnasium.spaces import Box,Discrete
import numpy as np
import torch
from sb3_contrib import MaskablePPO
from stable_baselines3.common.logger import configure
from agents.tactics import candidates as old_candidates,commands
from .candidate_policy import vector as old_vector
from .mission_features import vector,OBS_SIZE
from .mission_policy import MissionPolicy,export
from .mission_env import MissionEnv

class ShapeEnv(gym.Env):
    observation_space=Box(-4,4,(OBS_SIZE,),np.float32)
    action_space=Discrete(65)
    def reset(self,seed=None,options=None):super().reset(seed=seed);return np.zeros(OBS_SIZE,np.float32),{}
    def step(self,a):return np.zeros(OBS_SIZE,np.float32),0.,False,False,{}
    def action_masks(self):return np.ones(65,dtype=bool)

def initialize(seed=0):
    model=MaskablePPO(MissionPolicy,ShapeEnv(),n_steps=64,batch_size=32,n_epochs=2,gamma=.99**(1/3),gae_lambda=.95**(1/3),seed=seed,device='cpu',verbose=0)
    model.set_logger(configure(folder=None,format_strings=[]));return model

def identity(c):return tuple(c['command'][k] for k in ('op','unit','target','arg0','arg1'))

def distill(source,output,seed=0,rounds=64,epochs=10):
    # No held-out seed enters this collector. Each source initializes only its own successor.
    with np.load(source,allow_pickle=False) as d:
        if str(d['contract'])!='tactics-2' or str(d['rules_version'])!='combined-arms-4':raise ValueError('migration source must be tactics-2/rules4')
        weights={k:d[k].copy() for k in ('w0','b0','w1','b1','wo','bo')}
    model=initialize(seed);env=MissionEnv();env.reset(seed%1000);dataset=[];matched=0
    for n in range(rounds):
        for a in ('A','B'):
            obs=env.raw(a);old=old_candidates(obs);new=env.items[a];lookup={identity(c):c['id'] for c in new};pairs=[(c['id'],lookup[identity(c)]) for c in old if identity(c) in lookup]+[(64,64)]
            x=old_vector(obs,old);z=np.tanh(x@weights['w0'].T+weights['b0']);z=np.tanh(z@weights['w1'].T+weights['b1']);logits=z@weights['wo'].T+weights['bo'];old_ids,new_ids=map(list,zip(*pairs));target=torch.softmax(torch.tensor(logits[old_ids]),0)
            dataset.append((torch.tensor(vector(obs,new)[None]),torch.tensor(new_ids),target));matched+=len(pairs)-1
        before=env.engine.world.tick
        while env.agents and env.engine.world.tick==before:env.step({a:env.heuristic(a) for a in env.agents})
        if not env.agents:env.reset((seed+n+1)%1000)
    actor=[p for name,p in model.policy.mlp_extractor.named_parameters() if name.startswith('pi_')];optimizer=torch.optim.Adam(actor,lr=3e-4);initial=None
    for epoch in range(epochs):
        losses=[]
        for x,ids,target in dataset:
            prediction=model.policy.mlp_extractor.forward_actor(x)[0,ids];loss=torch.nn.functional.kl_div(torch.log_softmax(prediction,0),target,reduction='sum');optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(actor,.5);optimizer.step();losses.append(float(loss.detach()))
        mean=float(np.mean(losses))
        if initial is None:initial=mean
    # Distillation optimizer is deliberately discarded; PPO optimizer remains empty.
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True);model.save(path);export(model,path.with_suffix('.npz'))
    report=dict(source_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),contract='tactics-3',source_contract='tactics-2',training_seeds_only=True,rounds=rounds,matched=matched,kl_initial=initial,kl_final=mean if epochs else None,critic_fresh=True,optimizer_fresh=not bool(model.policy.optimizer.state))
    path.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');return model,report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');p.add_argument('--seed',type=int,default=0);p.add_argument('--rounds',type=int,default=64);a=p.parse_args();_,r=distill(a.source,a.output,a.seed,a.rounds);print(json.dumps(r))
