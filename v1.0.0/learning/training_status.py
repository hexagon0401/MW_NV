"""Small public progress report; never exports host paths or credentials."""
import json,os,time,sqlite3
from pathlib import Path
from datetime import datetime,timezone
from collections import deque

class Reporter:
    def __init__(self,root,round,base_steps=0):
        self.root=Path(root);self.round=round;self.base_steps=base_steps;self.start=time.monotonic();self.last=0;self.state={}
        self.evaluation_sim_seconds=0.;self.speed_phase='learning';self.samples=deque([(self.start,0.)])
    def advance_simulation(self,seconds,phase='evaluation'):
        """Count evaluation ticks without changing training progress or policy steps."""
        if phase!='evaluation' or seconds<0:raise ValueError('invalid evaluation increment')
        self.evaluation_sim_seconds+=seconds

    def _speed(self,now,phase,counter):
        if phase!=self.speed_phase or counter<self.samples[-1][1]:
            self.speed_phase=phase;self.samples=deque([(now,counter)])
            return None,0.
        if now>self.samples[-1][0]:self.samples.append((now,counter))
        cutoff=now-60
        while len(self.samples)>2 and self.samples[1][0]<=cutoff:self.samples.popleft()
        start,value=self.samples[0]
        if start<cutoff and len(self.samples)>1:
            end,next_value=self.samples[1]
            value+=(next_value-value)*(cutoff-start)/(end-start);start=cutoff
        elapsed=now-start
        return (round((counter-value)/elapsed,1) if elapsed>0 else None),elapsed

    def __call__(self,values=None,force=False):
        if values:self.state.update(values)
        now=time.monotonic()
        if not force and now-self.last<30:return
        self.last=now
        doc=dict(schema=1,status='running',updated_at=datetime.now(timezone.utc).isoformat(),round=self.round+1,completed_steps=self.base_steps);doc.update(self.state)
        phase='evaluation' if doc.get('phase')=='evaluation' else 'learning'
        counter=self.evaluation_sim_seconds if phase=='evaluation' else doc.get('sim_seconds',0)
        speed,window=self._speed(now,phase,counter)
        if doc.get('phase')=='stopped':speed=None
        doc.update(sim_speed=speed,sim_speed_basis='recent_phase_wall_time',speed_phase=phase,speed_window_seconds=round(window,1),evaluation_sim_seconds=self.evaluation_sim_seconds,device='CPU',algorithm=doc.get('algorithm','MaskablePPO'),maps=doc.get('maps','4 terrain variants'),replay_speed=1,nim_in_training=doc.get('nim_in_training',False))
        tmp=self.root/'training-status.partial';tmp.write_text(json.dumps(doc));tmp.replace(self.root/'training-status.json')
        Path('data/training-status.json').write_text(json.dumps(doc))
        if os.environ.get('MW_NV_PUBLISH_TRAINING')=='1':
            try:
                from cloud.supabase_storage import PrivateStorage
                store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY'])
                store._request('object/'+store.bucket+'/training-status.json','PUT',json.dumps(doc).encode())
                from .public_results import publish
                publish()
            except (OSError,ValueError,KeyError,sqlite3.Error) as exc:print('Training status upload deferred: '+type(exc).__name__,flush=True)
