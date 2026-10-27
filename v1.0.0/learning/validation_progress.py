"""Observer-only validation journal progress and heartbeats, independent of game RNG."""
import threading,time
from pathlib import Path
from engine.runtime import Engine
from engine.replay import decode
from engine.orders import OrderError
from .self_play import atomic_json

class CaseProgress:
    def __init__(self,root,mode,seed,swapped,outer):
        self.path=Path(root)/'audit-current.json';self.outer=outer;self.data=dict(case=f'{mode}:{seed}:{int(swapped)}',scenario_id=mode,seed=seed,swapped=swapped,phase='simulation',state='RUNNING',sim_seconds=0.,time_limit_seconds=3600 if mode!='2' else 2700)
        self.stop=threading.Event();self.guard=threading.Lock();self.thread=None
    def write(self,**values):
        with self.guard:self.data.update(values);atomic_json(self.path,dict(self.data,updated_at=time.time()))
    def __enter__(self):
        self.write()
        def beat():
            while not self.stop.wait(15):self.write()
        self.thread=threading.Thread(target=beat,daemon=True);self.thread.start();return self
    def case_tick(self,tick):self.write(sim_seconds=tick*.2)
    def __call__(self,*args):
        if self.outer:self.outer(*args)
    def __exit__(self,typ,*_):
        self.stop.set();self.thread.join();self.write(state='INTERRUPTED' if typ else 'COMPLETED')


def replay(document,progress):
    # Same journal operations as engine.replay.replay; only observation is additional.
    from engine.version import RULES_VERSION,CATALOG_VERSION
    if document.get('version')!=2 or (document.get('rules_version'),document.get('catalog_version')) not in ((RULES_VERSION,CATALOG_VERSION),('combined-arms-6','combined-arms-3')):raise ValueError('incompatible replay')
    e=Engine(decode(document['initial']));total=len(document['journal']);last=0.
    progress.write(phase='replay',journal_completed=0,journal_total=total,sim_seconds=0.)
    for index,action in enumerate(document['journal'],1):
        if action['kind']=='submit':
            try:e.submit(decode(action['value']))
            except OrderError:pass
        elif action['kind']=='step':e.step(action['value'])
        elif action['kind']=='event':e.world.emit(action['value'][0],**action['value'][1])
        else:raise ValueError('invalid replay operation')
        if time.monotonic()-last>=2 or index==total:
            progress.write(journal_completed=index,journal_total=total,sim_seconds=e.world.tick*.2);progress('replay');last=time.monotonic()
    if e.world.checksum()!=document['checksum']:raise ValueError('replay checksum mismatch')
    return e.world
