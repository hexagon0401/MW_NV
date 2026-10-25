from engine.version import RULES_VERSION
"""Explicit CPU training and held-out evaluation for combined-arms candidates."""
import argparse,json,uuid,os
from pathlib import Path
import gymnasium as gym
import numpy as np
import torch
from sb3_contrib import MaskablePPO
from .candidate_env import CandidateEnv
from .candidate_policy import CandidatePolicy,export


class TrainingEnv(gym.Env):
    def __init__(self,controlled='A',opponent=None,stats=None,seed_offset=0):
        from .training_maps import training_scenario
        self.seed_offset=seed_offset;self.sim_seconds=0;self.games=0
        self.parallel=CandidateEnv(scenario_factory=training_scenario);self.controlled=controlled;self.other='B' if controlled=='A' else 'A';self.opponent=CandidatePolicy(opponent) if opponent else None;self.episode=0;self.stats=stats;self.run_id='training-'+uuid.uuid4().hex
        self.observation_space=self.parallel.observation_space(controlled);self.action_space=self.parallel.action_space(controlled)
    def reset(self,seed=None,options=None):
        super().reset(seed=seed);chosen=(self.episode+self.seed_offset)%50 if seed is None else seed%50;self.episode+=1
        obs,_=self.parallel.reset(chosen,options=dict(swap=bool(self.episode%2)))
        from engine.viewer_export import frame
        self.initial_frame=frame(self.parallel.engine.world)
        return obs[self.controlled],{}
    def action_masks(self):return self.parallel.mask(self.controlled)
    def step(self,action):
        e=self.parallel;other=self.opponent.predict(e.vector(self.other),e.mask(self.other)) if self.opponent else e.heuristic(self.other)
        before=e.engine.world.tick
        obs,rewards,done,trunc,infos=e.step({self.controlled:int(action),self.other:other})
        self.sim_seconds+=(e.engine.world.tick-before)*.2
        if done[self.controlled]:self.games+=1
        if done[self.controlled] and self.stats:
            from .results import record_world
            record_world(self.stats,e.engine.world,'training',{self.controlled:self.run_id,self.other:self.opponent.policy_id if self.opponent else 'algorithm'},steps=0)
        if done[self.controlled] and os.environ.get('MW_NV_PUBLISH_TRAINING')=='1':
            try:
                from .replay_sink import publish_latest
                publish_latest(e.engine,self.initial_frame)
            except (OSError,ValueError,KeyError) as exc:print('Training replay upload deferred: '+type(exc).__name__,flush=True)
        return obs[self.controlled],rewards[self.controlled],done[self.controlled],trunc[self.controlled],infos[self.controlled]


def train(output,steps=64,controlled='A',opponent=None,seed=0,stats='data/results.sqlite',resume=None,progress=None):
    if steps<64:raise ValueError('steps >= 64')
    torch.set_num_threads(2);env=TrainingEnv(controlled,opponent,stats,seed_offset=seed)
    model=MaskablePPO.load(resume,env=env,device='cpu') if resume else MaskablePPO('MlpPolicy',env,n_steps=64,batch_size=32,n_epochs=2,policy_kwargs={'net_arch':{'pi':[128,128],'vf':[128,128]}},seed=seed,device='cpu',verbose=0)
    model.set_random_seed(seed)
    from stable_baselines3.common.callbacks import BaseCallback
    class Report(BaseCallback):
        def _on_step(self):
            if progress:progress(dict(policy_steps=self.num_timesteps,sim_seconds=env.sim_seconds,games=env.games,map_family=getattr(env.parallel.engine.world,'training_map_family','custom')))
            return True
    model.learn(total_timesteps=steps,reset_num_timesteps=not bool(resume),callback=Report());path=Path(output);path.parent.mkdir(parents=True,exist_ok=True);model.save(str(path));export(model,path.with_suffix('.npz'))
    obs,_=env.reset(seed=7);mask=env.action_masks();action,_=model.predict(obs,deterministic=True,action_masks=mask)
    loaded=MaskablePPO.load(str(path),device='cpu');check,_=loaded.predict(obs,deterministic=True,action_masks=mask)
    assert int(action)==int(check)==CandidatePolicy(path.with_suffix('.npz')).predict(obs,mask)
    path.with_suffix('.json').write_text(json.dumps(dict(contract='tactics-1',rules_version=RULES_VERSION,steps=steps,policy_steps=model.num_timesteps,resumed_from=resume,seed=seed,controlled=controlled,opponent=opponent,selected=False,policy_id=CandidatePolicy(path.with_suffix('.npz')).policy_id,training_run=env.run_id),indent=2)+'\n')
    if stats:
        from .results import record_training
        record_training(stats,CandidatePolicy(path.with_suffix('.npz')).policy_id,steps,env.opponent.policy_id if env.opponent else 'algorithm',training_run=env.run_id)
    return model


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='data/candidates/policy0');p.add_argument('--steps',type=int,default=64);p.add_argument('--opponent');p.add_argument('--controlled',choices=['A','B'],default='A');p.add_argument('--seed',type=int,default=0);a=p.parse_args();train(a.output,a.steps,a.controlled,a.opponent,a.seed);print('Candidate CPU training/save/load/NumPy parity PASS')
