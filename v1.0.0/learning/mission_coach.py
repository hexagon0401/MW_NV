"""Durable one-worker teacher jobs; only demonstration labels enter PPO buffers."""
import gzip,json,os,subprocess,sys,time,signal
from pathlib import Path
from engine.replay import encode
from .mission_env import MissionTeacher
from .self_play import atomic_json


def cpu(pid):
    try:
        fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
        return (int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK')
    except (OSError,ValueError,IndexError):return 0.

class MissionCoach:
    def __init__(self,root):
        self.root=Path(root)/'coaching';self.root.mkdir(parents=True,exist_ok=True);self.path=self.root/'state.json'
        try:self.state=json.loads(self.path.read_text())
        except (OSError,ValueError):self.state=dict(scheduled=0,jobs=[],completed=0,imported={},cpu_history=[],training_history=[])
        self.process=None;self.current=None;self.cpu_last={};self.stats={};self.recover_labels=True
        # A crashed coordinator must not leave a writer mutating its recovery files.
        worker=self.state.get('worker')
        if worker:
            from server.telemetry import process_start
            pid=worker['pid'];cmd=Path(f'/proc/{pid}/cmdline')
            def owns():
                try:
                    args=cmd.read_bytes().split(b'\0');directory=args[args.index(b'--directory')+1].decode()
                    return process_start(pid)==worker['start'] and b'learning.demonstrations' in args and (Path(f'/proc/{pid}/cwd')/directory).resolve()==(self.root/worker['job']).resolve()
                except (OSError,ValueError,IndexError):return False
            if owns():
                os.kill(pid,signal.SIGTERM);deadline=time.monotonic()+45
                while owns() and time.monotonic()<deadline:time.sleep(.05)
                if owns():raise RuntimeError('teacher worker still saving; preserve files and retry resume')
            self.state.pop('worker',None)
        # Imported cursors belong to the model/buffer checkpoint, not a newer job journal.
        pointer=Path(root)/'current.json'
        if pointer.exists():
            saved=Path(root)/json.loads(pointer.read_text())['path']/'coaching/state.json'
            self.state['imported']=json.loads(saved.read_text()).get('imported',{}) if saved.exists() else {}
        self._save()
    def _save(self):atomic_json(self.path,self.state)
    def schedule(self,games):
        while self.state['scheduled']<games//10:
            number=self.state['scheduled'];self.state['scheduled']+=1
            job=dict(id=f'demo-{number:08d}',scenario_id='3' if number%2==0 else '4',seed=4000+number%1000,swap=bool((number//4)%2),kind='demonstration',swap_learners=bool((number//2)%2))
            self._job(job)
        self._save()
    def _job(self,job,world=None):
        folder=self.root/job['id'];folder.mkdir(exist_ok=True);job.setdefault('run_id','coach-'+__import__('hashlib').sha256(str(self.root.parent.resolve()).encode()).hexdigest()[:12]);atomic_json(folder/'job.json',job)
        if world is not None:(folder/'world.json.gz').write_bytes(gzip.compress(json.dumps(encode(world),separators=(',',':')).encode(),compresslevel=1))
        self.state['jobs'].append(job['id'])
    def failure(self,world,reason,assignments=None):
        if getattr(world,'mode','conquest') not in ('elimination','capture_flag'):return
        # Deduplicate by mission and failure category. No evaluation worlds enter here.
        assignments=assignments or {'A':'PPO1','B':'PPO2'}
        signature=__import__('hashlib').sha256(json.dumps(assignments,sort_keys=True).encode()).hexdigest()[:6]
        key=f'failure-{world.scenario_id}-{reason}-{signature}'
        if key in self.state.get('failure_keys',[]):return
        self.state.setdefault('failure_keys',[]).append(key);self.state['failure_keys']=self.state['failure_keys'][-100:]
        recent=[j for j in self.state['jobs'] if j.startswith('failure-')]
        if len(recent)>=100:return
        self._job(dict(id=key,scenario_id=world.scenario_id,seed=world.seed,swap=getattr(world,'swapped',False),kind='failure_replay',reason=reason,assignments=assignments,swap_learners=False),world);self._save()
    def running(self):return self.process is not None and self.process.poll() is None
    def import_labels(self,folder,buffers):
        if not (folder/'samples.npz').exists():return
        labels=MissionTeacher();labels.load(folder/'samples.npz');done=self.state['imported'].get(folder.name,[-1,-1,-1])
        if not isinstance(done,list):done=[-1,-1,-1]
        job=json.loads((folder/'job.json').read_text())
        keys=[]
        for row in labels.rows:
            meta=row[4];key=[int(meta.get('tick',0)),int(row[3]),int(meta.get('prefix',0))]
            if key>done:
                learner=job.get('assignments',{}).get(('A','B')[int(row[3])])
                if learner is None:learner='PPO'+str((int(row[3])^int(job['swap_learners']))+1)
                if learner in ('PPO1','PPO2'):buffers[int(learner[-1])-1].rows.append(row)
            keys.append(key)
        self.state['imported'][folder.name]=max([done,*keys])
    def poll(self,buffers,pids,paused=False):
        if self.recover_labels:
            for folder in sorted(p for p in self.root.iterdir() if p.is_dir()):
                self.import_labels(folder,buffers)
                saved=folder/'slice.json'
                if folder.name in self.state['jobs'] and saved.exists() and json.loads(saved.read_text()).get('ended'):
                    self.state['jobs'].remove(folder.name);self.state['completed']+=1
            self.recover_labels=False
        now=time.time();history=self.state['training_history'];increment=0.
        for pid in pids:
            value=cpu(pid);increment+=max(0,value-self.cpu_last.get(pid,value));self.cpu_last[pid]=value
        history.append([now,increment]);self.state['training_history']=[r for r in history if r[0]>=now-1800]
        if self.process is not None and self.process.poll() is not None:
            folder=self.root/self.current
            try:result=json.loads((folder/'slice.json').read_text())
            except (OSError,ValueError):result={}
            # Include interpreter/import/write CPU even when no useful samples arrived.
            spent=max(self.last_cpu,float(result.get('cpu_seconds',0)),4 if self.process.returncode else 0)
            if self.process.returncode:self.state.update(worker_error='worker_exit_'+str(self.process.returncode),retry_after=now+300)
            self.state['cpu_history'].append([now,spent])
            if (folder/'progress.json').exists():self.state.setdefault('job_metrics',{})[self.current]=json.loads((folder/'progress.json').read_text())
            self.import_labels(folder,buffers)
            if result.get('ended'):
                if self.current in self.state['jobs']:self.state['jobs'].remove(self.current)
                self.state['completed']+=1
            self.state.pop('worker',None)
            self.process=None;self.current=None
        self.state['cpu_history']=[r for r in self.state['cpu_history'] if r[0]>=now-1800]
        spent=sum(r[1] for r in self.state['cpu_history']);training=sum(r[1] for r in self.state['training_history'])
        live=cpu(self.process.pid) if self.running() else 0.;self.last_cpu=live
        allowance=max(0,training/9-spent-live)
        pending=Path('data/nim-budget/demonstration-pending');pending.parent.mkdir(parents=True,exist_ok=True)
        if paused:
            if self.running():self.process.terminate()
            pending.unlink(missing_ok=True)
        elif not self.running() and self.process is None and self.state['jobs'] and now>=self.state.get('retry_after',0) and allowance>=5 and __import__('learning.adaptive_resources',fromlist=['resources']).resources()['memory_free_fraction']>=.2 and __import__('learning.adaptive_resources',fromlist=['resources']).resources()['cpu_budget']>=3:
            self.current=self.state['jobs'][0];pending.touch()
            log=(self.root/'worker.log').open('ab')
            self.process=subprocess.Popen([sys.executable,'-u','-m','learning.demonstrations','--directory',str(self.root/self.current),'--cpu-seconds',str(min(60,max(1,allowance-4)))],stdout=log,stderr=log,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'));log.close();self.last_cpu=0.
            from server.telemetry import process_start
            self.state['worker']=dict(pid=self.process.pid,start=process_start(self.process.pid),job=self.current)
        elif self.running():pending.touch()
        else:pending.unlink(missing_ok=True)
        job_metrics=list(self.state.get('job_metrics',{}).values())
        self.stats=dict(teacher_pairs=sum(m.get('paired',0) for m in job_metrics),teacher_samples=sum(m.get('samples',0) for m in job_metrics),stage_events={name:sum(m.get('stage_events',{}).get(name,0) for m in job_metrics) for name in ('UNIT_RESUPPLIED','DISEMBARK_DONE','BUILDING_ENTERED','FLAG_STOLEN','FLAG_RETURNED')},pending=len(self.state['jobs']),completed=self.state['completed'],cpu_seconds=spent+live,cpu_fraction=(spent+live)/max(1,training+spent+live),state='RUNNING' if self.running() else 'PAUSED' if paused else 'ERROR_BACKOFF' if now<self.state.get('retry_after',0) else 'WAITING_CPU_BUDGET',source='NIM separate demonstrations')
        self._save();return self.stats
    def prune(self):
        completed=[p for p in self.root.iterdir() if p.is_dir() and p.name not in self.state['jobs']]
        for folder in sorted(completed,key=lambda p:p.stat().st_mtime,reverse=True)[2:]:
            import shutil
            shutil.rmtree(folder)
    def close(self):
        if self.running():self.process.terminate();self.process.wait(timeout=45)
        Path('data/nim-budget/demonstration-pending').unlink(missing_ok=True)
