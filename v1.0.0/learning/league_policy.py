"""Independent masked PPO actors with simulation-time GAE and fresh migration."""
import random
from pathlib import Path
import numpy as np
import torch
from sb3_contrib import MaskablePPO
from sb3_contrib.common.maskable.buffers import MaskableRolloutBuffer
from stable_baselines3.common.logger import configure
from .candidate_train import TrainingEnv
from .candidate_policy import export


def initialize(source,seed):
    model=MaskablePPO('MlpPolicy',TrainingEnv(stats=None),n_steps=64,batch_size=32,n_epochs=2,gamma=.99**(1/3),gae_lambda=.95**(1/3),policy_kwargs={'net_arch':{'pi':[128,128],'vf':[128,128]}},seed=seed,device='cpu',verbose=0)
    with np.load(source,allow_pickle=False) as d:
        if str(d['contract']) not in ('tactics-1','tactics-2'):raise ValueError('actor source contract')
        if str(d['rules_version']) not in ('combined-arms-3','combined-arms-4'):raise ValueError('actor source rules')
        state=model.policy.state_dict()
        for key,destination in [('w0','mlp_extractor.policy_net.0.weight'),('b0','mlp_extractor.policy_net.0.bias'),('w1','mlp_extractor.policy_net.2.weight'),('b1','mlp_extractor.policy_net.2.bias'),('wo','action_net.weight'),('bo','action_net.bias')]:
            value=d[key]
            if value.shape!=tuple(state[destination].shape) or not np.isfinite(value).all():raise ValueError('actor source shape/value')
            state[destination]=torch.as_tensor(value.copy())
        model.policy.load_state_dict(state)
    assert not model.policy.optimizer.state
    model.set_logger(configure(folder=None,format_strings=[]));return model


def choose(model,observation,mask,generator=None,deterministic=False):
    model.policy.set_training_mode(False)
    obs=torch.as_tensor(observation[None],dtype=torch.float32)
    with torch.no_grad():
        dist=model.policy.get_distribution(obs,action_masks=mask[None])
        action=dist.mode() if deterministic else torch.multinomial(dist.distribution.probs,1,generator=generator).flatten()
        value=model.policy.predict_values(obs)
        logp=dist.log_prob(action)
    return int(action.item()),float(value.item()),float(logp.item())


def advantages(rows,last_value=0):
    result=np.zeros(len(rows),dtype=np.float32);following=0.
    for i in range(len(rows)-1,-1,-1):
        row=rows[i];next_value=rows[i+1]['value'] if i+1<len(rows) else last_value
        live=not row['terminal'];discount=.99**(1/3) if row['advance'] else 1.;trace=.95**(1/3) if row['advance'] else 1.
        delta=row['reward']+discount*next_value*live-row['value']
        following=delta+discount*trace*live*following;result[i]=following
    return result


def update(model,rows,last_value,teacher):
    if not rows:return dict(steps=0,imitation=None)
    buffer=MaskableRolloutBuffer(len(rows),model.observation_space,model.action_space,device='cpu',n_envs=1)
    for row in rows:
        buffer.add(row['obs'][None],np.array([row['action']]),np.array([row['reward']]),np.array([row['start']]),torch.tensor([row['value']]),torch.tensor([row['logp']]),action_masks=row['mask'][None])
    values=np.array([r['advantage'] for r in rows],dtype=np.float32) if all('advantage' in r for r in rows) else advantages(rows,last_value);buffer.advantages[:,0]=values;buffer.returns[:,0]=values+buffer.values[:,0]
    if not np.isfinite(buffer.returns).all():raise ValueError('nonfinite PPO return')
    model.rollout_buffer=buffer;model.num_timesteps+=len(rows);model._current_progress_remaining=1.
    # A minibatch of one makes SB3 advantage std undefined. Use whole batches if needed.
    model.batch_size=next((n for n in range(min(32,len(rows)),1,-1) if len(rows)%n!=1),len(rows))
    if len(rows)<2:model.normalize_advantage=False
    model.train();model.normalize_advantage=True
    loss=None
    if len(teacher.rows)>=32:
        batch=random.sample(list(teacher.rows),32);obs=torch.as_tensor(np.stack([r[0] for r in batch]));actions=torch.tensor([r[2] for r in batch]);masks=np.stack([r[1] for r in batch])
        _,logp,_=model.policy.evaluate_actions(obs,actions,action_masks=masks)
        objective=-.05*logp.mean();model.policy.optimizer.zero_grad();objective.backward();torch.nn.utils.clip_grad_norm_(model.policy.parameters(),.5);model.policy.optimizer.step();loss=float(objective.detach())
        teacher.stats['imitation_updates']=teacher.stats.get('imitation_updates',0)+1
    if any(not torch.isfinite(p).all() for p in model.policy.parameters()):raise ValueError('nonfinite policy')
    return dict(steps=len(rows),imitation=loss)


def schedule(block,seed=4701):
    import random
    rows=[]
    for team in ('A','B'):
        for swap in (False,True):
            rows.extend(dict(kind='duel',team=team,swap=swap,learner=0) for _ in range(4))
            for learner in (0,1):
                for kind in ('past','algorithm'):rows.append(dict(kind=kind,team=team,swap=swap,learner=learner))
    random.Random(seed+block).shuffle(rows)
    occurrences={}
    for i,row in enumerate(rows):
        key=(row['kind'],row['learner'],row['team'],row['swap']);n=occurrences.get(key,0);occurrences[key]=n+1
        row['seed']=(block*32+i)//4;row['family']=(block+n)%4
    return rows
