"""Manual, isolated frozen-policy comparison. Never updates or promotes a policy."""
import json,hashlib,os,sys,time,subprocess,fcntl
from pathlib import Path


def observe(spec,paths,content_digest):
    from server.release_observations import read
    root=Path(paths['root']);manifest=read(root/'manifest.json')
    valid=bool(manifest) and all((root/name).is_file() and hashlib.sha256((root/name).read_bytes()).hexdigest()==sha for name,sha in spec['artifact']['files'].items())
    if valid:
        from server.release_artifacts import verify
        try:verify(paths['runtime'],spec['artifact']['runtime_digest'])
        except (OSError,ValueError,KeyError):valid=False
    state=read(root/'job.json');current=None
    from server.telemetry import process_start
    for path in (root/'activity').glob('*.json'):
        row=read(path)
        if row.get('state')=='RUNNING' and row.get('process_start') is not None and row.get('process_start')==process_start(row.get('pid',0)):
            current={k:row.get(k) for k in ('match_id','sim_seconds','scenario_id')};break
    report=read(root/'evaluations/games-00000001/report.json')
    return dict(steps=[dict(id='artifacts',title='고정 정책·규칙·실행기 검증',state='PASS' if valid else 'FAIL',required=True)],blockers=[] if valid else ['COMPARISON_ARTIFACT_CHANGED'],connection='online',evidence_digest=content_digest if valid else None,comparison=dict(state=state.get('state','READY'),completed=len(report.get('results',[])),total=80,old_games=manifest.get('old_games'),new_games=manifest.get('new_games'),summary=state.get('summary'),current=current,replay_available=read(root/'latest-view.json').get('verified',False)))


class Comparison:
    def __init__(self,definition,registry):self.definition=definition;self.registry=registry;self.root=Path(definition['paths']['root'])
    def validate(self):
        from server.releases import digest
        if observe(self.definition['spec'],self.definition['paths'],digest(self.definition['spec']))['blockers']:raise ValueError('comparison artifacts changed')
    def prepare(self,journal,notify):notify(comparison_root=str(self.root))
    def switch(self,journal,notify):
        from server.telemetry import atomic,process_start
        from server.release_observations import read
        state=read(self.root/'job.json');info=read(self.root/'pid.json')
        if state.get('state')=='COMPLETED':return
        if info.get('pid') and process_start(info['pid'])==info.get('start') and Path(f"/proc/{info['pid']}/cmdline").exists() and str(self.root/'runner.py').encode() in Path(f"/proc/{info['pid']}/cmdline").read_bytes().split(b'\0'):return
        atomic(self.root/'job.json',dict(state='QUEUED',updated_at=time.time()))
        script=self.root/'runner.py';env=dict(os.environ,PYTHONPATH=self.definition['paths']['runtime'],MW_NV_PUBLISH_TRAINING='0',MW_NV_ACTIVITY_ROOT=str(self.root/'activity'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MW_NV_TORCH_THREADS='1',MPLCONFIGDIR='/tmp/mw-mpl')
        with (self.root/'job.log').open('ab') as log:p=subprocess.Popen([sys.executable,str(script),'--run',str(self.root)],cwd=self.root/'sandbox',env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
        atomic(self.root/'pid.json',dict(pid=p.pid,start=process_start(p.pid)));notify(job_started=True)
    def verify(self,journal):
        from server.release_observations import read
        if read(self.root/'job.json').get('state') not in ('QUEUED','WAITING_CPU','RUNNING','COMPLETED'):raise ValueError('comparison not accepted')
    def rollback(self,journal,notify):
        (self.root/'STOP').write_text('comparison canceled\n');notify(comparison_canceled=True)


def run(root):
    import torch
    from sb3_contrib import MaskablePPO
    from learning.league_evaluate import evaluate,paired_interval
    from server.telemetry import atomic,process_start
    root=Path(root);manifest=json.loads((root/'manifest.json').read_text());base=Path(manifest['base']);reservation=base/'data/releases/reservation.json'
    lock=(root/'job.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);torch.set_num_threads(1)
    global_lock=(base/'data/releases/comparison.lock').open('a');fcntl.flock(global_lock,fcntl.LOCK_EX)
    def progress(*_):
        if (root/'STOP').exists():raise InterruptedError('comparison canceled')
        atomic(reservation,dict(pid=os.getpid(),start=process_start(os.getpid()),cores=1,updated_at=time.time()))
        atomic(root/'job.json',dict(state='RUNNING',updated_at=time.time()))
    import threading
    stopped=threading.Event()
    def beat():
        while not stopped.wait(15):atomic(reservation,dict(pid=os.getpid(),start=process_start(os.getpid()),cores=1,updated_at=time.time()))
    heartbeat=threading.Thread(target=beat,daemon=True);heartbeat.start()
    original_record=None
    try:
        while True:
            progress()
            try:training=json.loads((base/'data/training-status.json').read_text())
            except (OSError,ValueError):training={}
            if training.get('workers',0)<=2 or training.get('phase')=='evaluation':break
            atomic(root/'job.json',dict(state='WAITING_CPU',updated_at=time.time()));time.sleep(5)
        import learning.league_evaluate as evaluator
        original_record=evaluator.record_world
        def record(db,w,mode,policies,**kwargs):
            result=original_record(db,w,mode,policies,**kwargs)
            try:
                import gzip
                from engine.runtime import Engine
                from engine.viewer_export import export_view
                from cloud.supabase_storage import PrivateStorage
                doc=export_view(Engine(w),kwargs['initial_frame'])
                assignments=kwargs['metadata']['league']['assignments'];learner=next(v for v in assignments.values() if v.startswith('PPO'))
                doc['comparison']=dict(teams={t:(f"최신 {manifest['new_games']}경기 {v}" if v.startswith('PPO') else f"과거 {manifest['old_games']}경기 {learner}" if v=='initial' else '규칙 HQ') for t,v in assignments.items()})
                body=json.dumps(doc,separators=(',',':')).encode();sha=hashlib.sha256(body).hexdigest();release_id=manifest['release_id'];key=f'comparisons/{release_id}/{sha}.json.gz';packed=gzip.compress(body,mtime=0)
                if len(packed)>16*1024**2:raise ValueError('comparison view exceeds limit')
                store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY']);store._request('object/'+store.bucket+'/'+key,'PUT',packed)
                assert hashlib.sha256(gzip.decompress(store._request('object/authenticated/'+store.bucket+'/'+key))).hexdigest()==sha
                pointer=dict(key=key,sha256=sha,verified=True)
                store._request('object/'+store.bucket+f'/comparisons/{release_id}/latest.json','PUT',json.dumps(pointer).encode());atomic(root/'latest-view.json',pointer)
                history=root/'view-history.json';old=json.loads(history.read_text()) if history.exists() else []
                keep=[key,*[x for x in old if x!=key]][:3];atomic(history,keep)
                expired=[x for x in old if x not in keep]
                if expired:store._request('object/'+store.bucket,'DELETE',json.dumps(dict(prefixes=expired)).encode())
            except Exception as e:atomic(root/'view-error.json',dict(reason=type(e).__name__))
            return result
        evaluator.record_world=record
        models=[MaskablePPO.load(root/f'ppo{i}.zip',device='cpu') for i in (1,2)]
        report=evaluate(root,models,dict(run='comparison-'+root.name,completed_games=1,generation=manifest['generation']),progress)
        summary={}
        for learner in ('PPO1','PPO2'):
            rows=[r for r in report['results'] if r['learner']==learner and r['opponent']=='initial'];groups={}
            for row in rows:groups.setdefault(row['seed'],[]).append(row['score'])
            interval=paired_interval([sum(v)/len(v) for v in groups.values()]);summary[learner]=dict(wins=sum(r['score']==1 for r in rows),draws=sum(r['score']==.5 for r in rows),losses=sum(r['score']==0 for r in rows),score_interval=interval)
        atomic(root/'job.json',dict(state='COMPLETED',updated_at=time.time(),summary=summary));
    except Exception as e:
        atomic(root/'job.json',dict(state='CANCELED' if isinstance(e,InterruptedError) else 'FAILED',reason=type(e).__name__,updated_at=time.time()));raise
    finally:
        stopped.set();heartbeat.join()
        if original_record is not None:evaluator.record_world=original_record
        try:
            if json.loads(reservation.read_text()).get('pid')==os.getpid():reservation.unlink()
        except (OSError,ValueError):pass

if __name__=='__main__':run(sys.argv[2])
