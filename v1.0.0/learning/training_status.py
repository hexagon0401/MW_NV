"""Small public progress report; never exports host paths or credentials."""
import json,os,time,sqlite3
from pathlib import Path
from datetime import datetime,timezone

class Reporter:
    def __init__(self,root,round,base_steps=0):
        self.root=Path(root);self.round=round;self.base_steps=base_steps;self.start=time.monotonic();self.last=0;self.state={}
    def __call__(self,values=None,force=False):
        if values:self.state.update(values)
        now=time.monotonic()
        if not force and now-self.last<30:return
        self.last=now;elapsed=now-self.start
        doc=dict(schema=1,status='running',updated_at=datetime.now(timezone.utc).isoformat(),round=self.round+1,completed_steps=self.base_steps);doc.update(self.state)
        doc.update(sim_speed=round(doc.get('sim_seconds',0)/max(.001,elapsed),1),device='CPU',algorithm='MaskablePPO',maps='4 terrain variants',replay_speed=1,nim_in_training=doc.get('nim_in_training',False))
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
