"""Balanced offline teacher labels and a separate actor-only imitation update."""
import os,time,random,json
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from agents.local_hq import LocalHQ
from agents.teacher import choose
from agents.tactics import shortlist,compatible
from .candidate_policy import vector

class TeacherBuffer:
    observation_size=1056
    encode=staticmethod(vector)
    def __init__(self):self.rows=deque(maxlen=10000);self.stats=dict(paired=0,skipped=0,requests=0);self.cooldown=0
    def save(self,path):
        rows=list(self.rows)
        np.savez_compressed(path,cooldown_until=np.array(time.time()+max(0,self.cooldown-time.monotonic())),x=np.array([r[0] for r in rows],dtype=np.float32).reshape(-1,self.observation_size),mask=np.array([r[1] for r in rows],dtype=bool).reshape(-1,65),action=np.array([r[2] for r in rows],dtype=np.int64),team=np.array([r[3] for r in rows],dtype=np.int8),metadata=np.array([json.dumps(r[4] if len(r)>4 else {},sort_keys=True) for r in rows],dtype=str))
    def load(self,path):
        with np.load(path,allow_pickle=False) as d:
            if d['x'].shape!=(len(d['action']),self.observation_size) or d['mask'].shape!=(len(d['action']),65) or not np.isfinite(d['x']).all():raise ValueError('teacher buffer contract')
            self.cooldown=time.monotonic()+max(0,float(d['cooldown_until'])-time.time()) if 'cooldown_until' in d else 0
            for i,row in enumerate(zip(d['x'],d['mask'],d['action'],d['team'])):self.rows.append((*row,json.loads(str(d['metadata'][i])) if 'metadata' in d else {}))
    def collect(self,env,clients=None):
        self.last_batches=None
        if time.monotonic()<self.cooldown:
            self.stats['skipped']+=1;self.stats['retry_in_seconds']=round(self.cooldown-time.monotonic(),1);return
        self.last_batches=None
        started=time.monotonic()
        try:
            if clients is None:clients=[LocalHQ('https://integrate.api.nvidia.com/v1',model='nvidia/nemotron-3.5-lightning-30b-a3b',timeout=30,api_key=os.environ.get('NVIDIA_API_KEY_A' if t==0 else 'NVIDIA_API_KEY_B')) for t in (0,1)]
            observations=[env.raw(a) for a in ('A','B')];self.stats['requests']+=2
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures=[pool.submit(choose,clients[t],observations[t],shortlist(env.items[a])) for t,a in enumerate(('A','B'))]
                batches=[f.result() for f in futures]
            staged=[]
            for team,(obs,a,batch) in enumerate(zip(observations,('A','B'),batches)):
                selected=[]
                for action in [c['id'] for c in batch]+([] if len(batch)==4 else [64]):
                    available=compatible(env.items[a],selected);mask=np.zeros(65,dtype=bool);mask[64]=True
                    for c in available:mask[c['id']]=True
                    if not mask[action]:raise ValueError('teacher mask')
                    from .decision_inputs import encode,REVISION
                    values=encode(obs,available,selected,mission=self.observation_size==1600)
                    chosen=next((c for c in available if c['id']==action),None)
                    staged.append((values,mask,action,team,dict(input_revision=REVISION,mode=obs.get('mission',{}).get('mode','conquest'),stage=chosen['role'] if chosen else 'end',prefix=len(selected),source=getattr(env,'teacher_source','ordinary'),tick=obs.get('tick',0))))
                    if action!=64:selected.append(next(c for c in available if c['id']==action))
            self.rows.extend(staged);self.last_batches=batches;self.stats['paired']+=1
            self.stats.update(consecutive_network_failures=0,last_error=None,last_error_code=None)
        except Exception as exc:
            # Teacher failures never create one-sided labels or stop PPO.
            self.stats['skipped']+=1
            if getattr(exc,'code',None)==429:
                try:delay=float(exc.headers.get('Retry-After','60'))
                except (TypeError,ValueError):
                    from email.utils import parsedate_to_datetime
                    try:delay=parsedate_to_datetime(exc.headers['Retry-After']).timestamp()-time.time()
                    except (ValueError,TypeError,KeyError):delay=60
                self.cooldown=time.monotonic()+max(1,delay)
            code=getattr(exc,'code',None)
            if (code is None and isinstance(exc,OSError)) or (code is not None and 500<=code<600):
                failures=min(4,self.stats.get('consecutive_network_failures',0)+1)
                self.stats['consecutive_network_failures']=failures
                self.cooldown=time.monotonic()+min(300,60*2**(failures-1))
            self.stats['last_error']=type(exc).__name__;self.stats['last_error_code']=code
        finally:
            self.stats['last_request_seconds']=round(time.monotonic()-started,3)
            self.stats['retry_in_seconds']=round(max(0,self.cooldown-time.monotonic()),1)
    def sample_rows(self):
        groups=[[r for r in self.rows if r[3]==t] for t in (0,1)]
        if min(map(len,groups))<16:return []
        return random.sample(groups[0],16)+random.sample(groups[1],16)
    def imitate(self,model):
        from .update_safety import imitate
        return imitate(model,self.sample_rows(),self.stats)

from sb3_contrib import MaskablePPO
class TeacherPPO(MaskablePPO):
    def _excluded_save_params(self):return super()._excluded_save_params()+['teacher_buffer']
    def train(self):
        super().train()
        if getattr(self,'teacher_buffer',None) is not None:
            loss=self.teacher_buffer.imitate(self)
            if loss is not None:
                self.logger.record('train/teacher_loss',loss);self.teacher_buffer.stats['last_imitation_loss']=loss
