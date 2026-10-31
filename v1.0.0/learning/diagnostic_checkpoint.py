"""Atomic diagnostic-only progress, including an interrupted journal replay."""
import gzip,hashlib,json,os,time
from pathlib import Path
from engine.replay import encode,decode,RecordingEngine
from engine.runtime import Engine


def dependencies():
    files=sorted(p for folder in ('engine','agents','config') for p in Path(folder).glob('*') if p.suffix in ('.py','.yaml') and str(p)!='config/releases.yaml')
    return hashlib.sha256(b''.join(str(p).encode()+p.read_bytes() for p in files)).hexdigest()


class DiagnosticCheckpoint:
    def __init__(self,root,case):
        self.root=Path(root)/'audit-checkpoints';self.root.mkdir(exist_ok=True)
        self.case=case.replace(':','-');self.identity=dependencies();self.last={}
    def path(self,phase):return self.root/(self.case+'.'+phase+'.json.gz')
    def load(self,phase):
        p=self.path(phase)
        if not p.exists():return None
        with gzip.open(p,'rt') as f:data=json.load(f)
        if data['dependencies']!=self.identity:raise ValueError('diagnostic checkpoint dependencies changed')
        world=decode(data['world'])
        if world.checksum()!=data['checksum']:raise ValueError('diagnostic checkpoint checksum mismatch')
        data['world']=world;return data
    def save(self,phase,world,force=False,**extra):
        if not force and world.tick-self.last.get(phase,-1500)<1500:return
        value=dict(dependencies=self.identity,world=encode(world),checksum=world.checksum(),**extra)
        path=self.path(phase);temporary=path.with_suffix('.partial')
        with temporary.open('wb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='wb',compresslevel=1,mtime=0) as zipped:
                zipped.write(json.dumps(value,separators=(',',':')).encode())
            raw.flush();os.fsync(raw.fileno())
        temporary.replace(path);self.last[phase]=world.tick
    def restore_simulation(self):
        data=self.load('simulation')
        if data is None:return None
        engine=RecordingEngine.__new__(RecordingEngine);Engine.__init__(engine,data['world'])
        engine.initial=data['initial'];engine.journal=data['journal'];engine.presentation_events=data['presentation_events']
        self.last['simulation']=engine.world.tick
        return engine,{int(k):v for k,v in data['history'].items()},data['decisions']
    def save_simulation(self,engine,history,decisions,force=False):
        self.save('simulation',engine.world,force,initial=engine.initial,journal=engine.journal,presentation_events=engine.presentation_events,history=history,decisions=decisions)
    def clear(self):
        for phase in ('simulation','replay'):self.path(phase).unlink(missing_ok=True)
