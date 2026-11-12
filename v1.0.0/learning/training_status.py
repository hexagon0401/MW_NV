"""Small public progress report; never exports host paths or credentials."""
import json,os,time,sqlite3,threading,uuid
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime,timezone
from collections import deque

class Reporter:
    def __init__(self,root,round,base_steps=0):
        self.root=Path(root);self.round=round;self.base_steps=base_steps;self.start=time.monotonic();self.last=0;self.state={}
        self.evaluation_sim_seconds=0.;self.speed_phase='learning';self.samples=deque([(self.start,0.)]);self.worker_samples={}
    @contextmanager
    def busy(self,phase='checkpoint',interval=15):
        """Heartbeat only; never reads models, engine pipes, or simulation RNG."""
        previous=self.state.get('phase','learning');started=time.monotonic();done=threading.Event()
        def heartbeat():self(dict(phase=phase,operation='recovery_save',operation_elapsed_seconds=round(time.monotonic()-started,1)),force=True)
        heartbeat()
        def pump():
            while not done.wait(interval):heartbeat()
        thread=threading.Thread(target=pump,name='checkpoint-heartbeat',daemon=True);thread.start()
        try:yield
        finally:
            done.set();thread.join()
            self(dict(phase=previous,operation=None,checkpoint_seconds=round(time.monotonic()-started,3)),force=True)

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
        phase=doc.get('phase') if doc.get('phase') in ('evaluation','checkpoint','paused','updating','stopped') else 'learning'
        counter=self.evaluation_sim_seconds if phase=='evaluation' else doc.get('sim_seconds',0)
        speed,window=self._speed(now,phase,counter)
        if phase not in ('learning','evaluation'):speed=None
        doc.update(sim_speed=speed,sim_speed_basis='recent_phase_wall_time',speed_phase=phase,speed_window_seconds=round(window,1),evaluation_sim_seconds=self.evaluation_sim_seconds,device='CPU',algorithm=doc.get('algorithm','MaskablePPO'),maps=doc.get('maps','4 terrain variants'),replay_speed=1,nim_in_training=doc.get('nim_in_training',False))
        worker_rates={}
        for worker,seconds in doc.get('worker_sim_seconds',{}).items():
            previous=self.worker_samples.get(worker)
            worker_rates[worker]=round((seconds-previous[1])/(now-previous[0]),1) if previous and now>previous[0] and phase=='learning' and previous[2]==phase else None
            self.worker_samples[worker]=(now,seconds,phase)
        if worker_rates:doc['worker_sim_speeds']=worker_rates
        tmp=self.root/'training-status.partial';tmp.write_text(json.dumps(doc));tmp.replace(self.root/'training-status.json')
        global_tmp=Path('data/training-status.'+uuid.uuid4().hex+'.partial');global_tmp.write_text(json.dumps(doc));global_tmp.replace('data/training-status.json')
        if os.environ.get('MW_NV_PUBLISH_TRAINING')=='1' and os.environ.get('MW_NV_ASYNC_IO')=='1':
            from .background_io import latest
            latest(self.root,'status',doc)
            return
        if os.environ.get('MW_NV_PUBLISH_TRAINING')=='1':
            try:
                from cloud.supabase_storage import PrivateStorage
                store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY'])
                store._request('object/'+store.bucket+'/training-status.json','PUT',json.dumps(doc).encode())
                from .public_results import publish
                publish()
            except (OSError,ValueError,KeyError,sqlite3.Error) as exc:print('Training status upload deferred: '+type(exc).__name__,flush=True)
