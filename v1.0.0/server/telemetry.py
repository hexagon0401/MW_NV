"""Opt-in process-owned activity snapshots; no changes to simulation or policy RNG."""
import json,os,time,uuid
from pathlib import Path

def atomic(path,doc):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.partial');tmp.write_text(json.dumps(doc,separators=(',',':')));tmp.replace(path)

def process_start(pid):
    try:return int(Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19])
    except (OSError,ValueError,IndexError):return None

class Activity:
    def __init__(self,role,match_id,run_id=None,scenario_id=None,learners=None):
        root=os.environ.get('MW_NV_ACTIVITY_ROOT');self.path=Path(root)/f'{os.getpid()}.json' if root else None;self.last=0.
        self.doc=dict(role=role,match_id=match_id,run_id=run_id,scenario_id=scenario_id,learners=learners or [],state='RUNNING',sim_seconds=0.,pid=os.getpid(),process_start=process_start(os.getpid()),started_at=time.time())
        self.update(force=True)
    def update(self,tick=None,state=None,force=False):
        if tick is not None:self.doc['sim_seconds']=tick*.2
        if state:self.doc['state']=state
        now=time.monotonic()
        if self.path and (force or now-self.last>=15):self.last=now;atomic(self.path,dict(self.doc,updated_at=time.time()))
    def close(self,state='COMPLETED'):self.update(state=state,force=True)
    def __enter__(self):return self
    def __exit__(self,*_):self.close()

def activities(root='data/activity'):
    result=[]
    for path in Path(root).glob('*.json'):
        try:
            d=json.loads(path.read_text());alive=process_start(d['pid'])==d['process_start'] and d['process_start'] is not None
            state=d['state']
            if not alive or state in ('COMPLETED','IDLE'):continue
            if time.time()-d['updated_at']>90 and state=='RUNNING':state='STALE'
            result.append({k:d.get(k) for k in ('role','match_id','run_id','scenario_id','learners','sim_seconds','started_at','updated_at')}|dict(state=state))
        except (OSError,ValueError,KeyError):continue
    return result

class Resources:
    def __init__(self):self.previous=None;self.process_previous=None
    def sample(self,pids=()):
        root=Path('/sys/fs/cgroup');now=time.monotonic();cpu=used=limit=budget=rss=None
        try:
            values=dict(line.split() for line in (root/'cpu.stat').read_text().splitlines());usage=int(values['usage_usec'])/1e6
            quota,period=(root/'cpu.max').read_text().split();budget=min(4,len(os.sched_getaffinity(0))) if quota=='max' else min(4,float(quota)/float(period))
            if self.previous:cpu=(usage-self.previous[1])/max(.001,now-self.previous[0])
            self.previous=(now,usage)
        except (OSError,ValueError,KeyError):pass
        try:used=int((root/'memory.current').read_text())/1024**2;raw=(root/'memory.max').read_text().strip();limit=int(raw)/1024**2 if raw!='max' else None
        except (OSError,ValueError):pass
        process_total=0.;process_known=False;process_cpu=None
        values=[]
        for pid in set(pids):
            try:
                # RSS from statm is available even when smaps_rollup is restricted.
                values.append(int(Path(f'/proc/{pid}/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')/1024**2)
                fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();process_total+=(int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK');process_known=True
            except (OSError,ValueError,IndexError):continue
        if not values and pids:
            try:
                import subprocess
                values=[int(v)/1024 for v in subprocess.check_output(['ps','-p',','.join(str(p) for p in pids),'-o','rss='],text=True).split()]
            except (OSError,ValueError,subprocess.CalledProcessError):pass
        if values:rss=sum(values)
        identities=tuple(sorted((pid,process_start(pid)) for pid in set(pids)))
        if process_known:
            if self.process_previous and identities==self.process_previous[2]:process_cpu=max(0.,(process_total-self.process_previous[1])/max(.001,now-self.process_previous[0]))
            self.process_previous=(now,process_total,identities)
        return dict(process_cpu_cores=process_cpu,cpu_cores=cpu,cpu_budget=budget,memory_used_mib=used,memory_limit_mib=limit,process_rss_mib=rss)
