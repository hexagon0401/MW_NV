"""Matched 20-action Random/Heuristic policies and NumPy MLP inference."""
from math import hypot
import numpy as np


def choose(env,agent,rng=None):
    mask=env.mask(agent);valid=np.flatnonzero(mask)
    if rng is not None:return int(rng.choice(valid))
    obs=env.raw(agent);groups=sorted(obs['squads'],key=lambda g:g['id']);slot=(obs['tick']//150)%4
    if not mask[slot*5:slot*5+5].any():slot=int(valid[0]//5)
    units={u['id']:u for u in obs['units']};members=[units[i] for i in groups[slot]['member_ids'] if units[i]['alive']]
    if not members:return int(valid[0])
    if any(u['type_id'] in ('INF','REC','SUP') and u['ammo']<3 for u in members) and obs['resources']['supply']>=6:return slot*5+3
    p=members[0]['pos'];targets=sorted((f for f in obs['facilities'] if f['kind']=='OBJECTIVE'),key=lambda f:f['id'])
    candidates=[(i,f) for i,f in enumerate(targets) if f['owner']!=obs['team']] or list(enumerate(targets))
    goal=min(candidates,key=lambda item:hypot(item[1]['pos']['x_cm']-p['x_cm'],item[1]['pos']['y_cm']-p['y_cm']))[0]
    return slot*5+goal


class NumpyPolicy:
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as data:self.weights={k:data[k] for k in data.files}
    def logits(self,obs):
        x=np.asarray(obs,dtype=np.float32)
        for i in range(2):x=np.tanh(x@self.weights[f'w{i}'].T+self.weights[f'b{i}'])
        return x@self.weights['wo'].T+self.weights['bo']
    def predict(self,obs,mask):
        if not np.any(mask):raise ValueError('no legal action')
        return int(np.argmax(np.where(mask,self.logits(obs),-np.inf)))


def export_numpy(model,path):
    p=model.policy.state_dict()
    arrays={}
    for i,layer in enumerate((0,2)):
        arrays[f'w{i}']=p[f'mlp_extractor.policy_net.{layer}.weight'].cpu().numpy()
        arrays[f'b{i}']=p[f'mlp_extractor.policy_net.{layer}.bias'].cpu().numpy()
    arrays['wo']=p['action_net.weight'].cpu().numpy();arrays['bo']=p['action_net.bias'].cpu().numpy()
    np.savez(path,**arrays)
