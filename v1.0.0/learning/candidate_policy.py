from engine.version import RULES_VERSION
"""Versioned 1056-feature / 65-action NumPy policy for hybrid tactical HQ."""
import hashlib
import numpy as np
from agents.tactics import CONTRACT

OBS_SIZE=1056
ACTIONS=65


def vector(obs,items):
    result=np.zeros(OBS_SIZE,dtype=np.float32)
    own=[u for u in obs['units'] if u['alive']];vehicles=[v for v in obs['vehicles'] if v['alive']]
    result[:12]=[len(own)/96,len(vehicles)/14,obs['resources']['credits']/5000,obs['resources']['supply']/2000,obs['resources']['tickets']/96,obs['scores'][obs['team']]/100,obs['scores'][1-obs['team']]/100,obs['tick']/15000,len(obs['enemies'])/128,len(items)/64,sum(u['carrier_id'] is not None for u in own)/96,0.]
    for i,f in enumerate(sorted((f for f in obs['facilities'] if f['kind']=='OBJECTIVE'),key=lambda f:f['id'])[:3]):result[12+i]=0 if f['owner'] is None else 1 if f['owner']==obs['team'] else -1
    history=obs.get('recent_summary',[])
    if history:result[18:18+min(14,len(history))]=history[:14]
    for c in items:result[32+c['id']*16:32+(c['id']+1)*16]=c['features']
    return np.clip(result,-1,1)


class CandidatePolicy:
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as data:
            if str(data['contract'].item())!=CONTRACT or str(data['rules_version'].item())!=RULES_VERSION:raise ValueError('policy contract mismatch')
            self.weights={k:data[k].copy() for k in ('w0','b0','w1','b1','wo','bo')}
        expected={'w0':(128,OBS_SIZE),'b0':(128,),'w1':(128,128),'b1':(128,),'wo':(ACTIONS,128),'bo':(ACTIONS,)}
        if any(self.weights[k].shape!=shape or not np.isfinite(self.weights[k]).all() for k,shape in expected.items()):raise ValueError('invalid policy shape/values')
        self.policy_id=hashlib.sha256(b''.join(self.weights[k].tobytes() for k in sorted(self.weights))).hexdigest()[:16]
    def logits(self,obs):
        x=np.asarray(obs,dtype=np.float32)
        if x.shape!=(OBS_SIZE,):raise ValueError('observation contract mismatch')
        for i in range(2):x=np.tanh(x@self.weights[f'w{i}'].T+self.weights[f'b{i}'])
        return x@self.weights['wo'].T+self.weights['bo']
    def predict(self,obs,mask):return int(np.argmax(np.where(mask,self.logits(obs),-np.inf)))


def export(model,path):
    p=model.policy.state_dict();data=dict(contract=np.array(CONTRACT),rules_version=np.array(RULES_VERSION))
    for i,layer in enumerate((0,2)):
        data[f'w{i}']=p[f'mlp_extractor.policy_net.{layer}.weight'].cpu().numpy();data[f'b{i}']=p[f'mlp_extractor.policy_net.{layer}.bias'].cpu().numpy()
    data['wo']=p['action_net.weight'].cpu().numpy();data['bo']=p['action_net.bias'].cpu().numpy()
    np.savez(path,**data)
