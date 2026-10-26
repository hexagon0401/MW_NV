"""Mac inference uses NumPy only; no Torch import or model deserialization."""
import hashlib
import numpy as np
CONTRACT="tactics-3"

class NumpyPolicy:
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as d:
            if str(d['contract'])!=CONTRACT or str(d['rules_version'])!='combined-arms-5':raise ValueError('mission policy contract')
            self.weights={k:d[k].copy() for k in d.files if k.startswith('pi_')}
        template={'pi_rows.0':(64,24),'pi_rows.2':(64,64),'pi_context.0':(128,64),'pi_context.2':(64,128),'pi_score.0':(64,256),'pi_score.2':(1,64),'pi_stop.0':(64,192),'pi_stop.2':(1,64)}
        shapes={key+suffix:shape if suffix=='.weight' else (shape[0],) for key,shape in template.items() for suffix in ('.weight','.bias')}
        if set(self.weights)!=set(shapes) or any(self.weights[k].shape!=shapes[k] or not np.isfinite(self.weights[k]).all() for k in self.weights):raise ValueError('mission policy weights')
        self.policy_id=hashlib.sha256(b''.join(self.weights[k].tobytes() for k in sorted(self.weights))).hexdigest()[:16]
    def layer(self,x,name,activation=True):
        x=x@self.weights[name+'.weight'].T+self.weights[name+'.bias'];return np.tanh(x) if activation else x
    def logits(self,obs):
        obs=np.asarray(obs,dtype=np.float32)
        if obs.shape!=(1600,):raise ValueError('mission observation size')
        raw=obs[64:].reshape(64,24);valid=np.abs(raw).sum(-1)>0;rows=self.layer(self.layer(raw,'pi_rows.0'),'pi_rows.2');context=self.layer(self.layer(obs[:64],'pi_context.0'),'pi_context.2');mean=(rows*valid[:,None]).sum(0)/max(1,valid.sum());maximum=rows[valid].max(0) if valid.any() else np.zeros(64,np.float32);global_features=np.concatenate((context,mean,maximum));scores=self.layer(self.layer(np.concatenate((rows,np.broadcast_to(global_features,(64,192))),-1),'pi_score.0'),'pi_score.2',False).ravel();stop=self.layer(self.layer(global_features,'pi_stop.0'),'pi_stop.2',False).ravel();return np.concatenate((scores,stop))
    def predict(self,obs,mask):return int(np.argmax(np.where(mask,self.logits(obs),-np.inf)))
