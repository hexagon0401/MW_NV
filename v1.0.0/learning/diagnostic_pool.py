"""Independent full matches on bounded CPU processes, durable per-case results."""
import json,multiprocessing,os,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
from .self_play import atomic_json
from .diagnostic_checkpoint import dependencies


def case(task):
    from .mission_evaluate import play
    from .validation_progress import CaseProgress,replay
    root,mode,seed=task;root=Path(root);folder=root/'audit-cases'/f'{mode}-{seed}';folder.mkdir(parents=True,exist_ok=True)
    identity=dependencies();cached=folder/'result.json'
    if cached.exists():
        result=json.loads(cached.read_text())
        if result['dependencies']==identity:return result['result']
    def progress(*_):
        if (root/'VALIDATION_STOP').exists():raise InterruptedError('validation safely paused')
    started=time.perf_counter()
    with CaseProgress(folder,mode,seed,bool(seed%2),progress) as observer:
        e,result=play(seed,mode,swap=bool(seed%2),progress=observer,record=True)
        simulated=time.perf_counter();result['replay_hash_verified']=replay(e.document(),observer).checksum()==result['hash']
    if not result['complete'] or not result['replay_hash_verified']:raise ValueError('incomplete diagnostic')
    result['diagnostic_timing']=dict(simulation_s=simulated-started,replay_s=time.perf_counter()-simulated)
    atomic_json(cached,dict(dependencies=identity,result=result));observer.checkpoint.clear();return result


def audit(root,count,progress,workers):
    root=Path(root);path=root/'engine-audit.json';report=json.loads(path.read_text()) if path.exists() else dict(complete=False,results=[])
    done={(r['scenario_id'],r['seed']) for r in report['results']};tasks=[(str(root.resolve()),mode,seed) for mode in ('2','3','4') for seed in range(count) if (mode,seed) not in done]
    with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        pending={pool.submit(case,t):t for t in tasks}
        while pending:
            completed,_=wait(pending,timeout=2,return_when=FIRST_COMPLETED)
            for future in completed:
                result=future.result();report['results'].append(result);atomic_json(path,report);del pending[future]
            running=[]
            for _,mode,seed in pending.values():
                p=root/'audit-cases'/f'{mode}-{seed}'/'audit-current.json'
                if p.exists():
                    row=json.loads(p.read_text())
                    if row['state']=='RUNNING':running.append(row)
            if running:
                atomic_json(root/'audit-current.json',running[0]);atomic_json(root/'audit-parallel.json',dict(workers=workers,cases=running,updated_at=time.time()))
            if progress:progress('diagnostic')
    report.update(complete=True,counts={m:sum(r['scenario_id']==m for r in report['results']) for m in ('2','3','4')});atomic_json(path,report);return report
