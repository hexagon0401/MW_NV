"""Explicit bootstrap plus a bounded, lease-gated recovery loop."""
import argparse,fcntl,json,os,signal,subprocess,sys,time
from pathlib import Path
from .telemetry import atomic,process_start
from .runtime_lease import Client,boot_id,lease_valid
from .release_artifacts import verify
from .release_observations import read
from .releases import Registry

BASE=Path(__file__).resolve().parents[1]

def alive(info,module,args=(),boot=None):
    if info.get('boot_id')!=(boot or boot_id()) or info.get('start') is None or process_start(info.get('pid',0))!=info['start']:return False
    try:
        cmd=Path(f'/proc/{info["pid"]}/cmdline').read_bytes().split(b'\0')
        return module.encode() in cmd and all(str(a).encode() in cmd for a in args)
    except OSError:return False

def find_running(module,args):
    for p in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            cmd=p.read_bytes().split(b'\0')
            if module.encode() in cmd and all(str(a).encode() in cmd for a in args):return dict(pid=int(p.parent.name),start=process_start(int(p.parent.name)),boot_id=boot_id())
        except OSError:pass
    return None

def restart_allowed(history,now):return len([t for t in history if now-900<t<=now])<3

def spawn(base,key,module,args):
    folder=base/'data/runtime';folder.mkdir(exist_ok=True)
    with (folder/(key+'.log')).open('ab') as log:p=subprocess.Popen([sys.executable,'-u','-m',module,*args],cwd=base,env=dict(os.environ,MW_NV_INSTALLATION_BASE=str(base),MW_NV_CONTROL_ROOT=str(base/'data/control'),MW_NV_ACTIVITY_ROOT=str(base/'data/activity'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MW_NV_TORCH_THREADS='1',MPLCONFIGDIR='/tmp/mw-mpl'),stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
    info=dict(pid=p.pid,start=process_start(p.pid),boot_id=boot_id());atomic(folder/(key+'.json'),info);return info

def blocked(base,root):
    pending=Registry(base/'data/releases').pending()
    own=read(base/'data/runtime/config.json').get('release_id')
    if pending and not (pending['release_id']==own and pending['phase']=='VERIFYING'):return 'release_in_progress'
    if read(base/'data/control/state.json').get('desired')=='paused':return 'administrator_paused'
    if (root/'STOP').exists():return 'owned_stop_marker'
    if read(root/'state.json').get('pause_reason'):return 'saved_pause_reason'
    return None

def supervise(base):
    folder=base/'data/runtime';folder.mkdir(exist_ok=True);lock=(folder/'supervisor.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cfg=read(folder/'config.json');root=Path(cfg['root']).resolve();runtime=Path(cfg['runtime']).resolve()
    if not root.is_relative_to(base/'data/releases/production') or not runtime.is_relative_to(base/'data/releases/artifacts'):raise ValueError('unregistered runtime')
    verify(runtime,cfg['runtime_digest']);active=read(base/'data/releases/active.json')
    if active.get('root')!=str(root) or active.get('runtime')!=str(runtime):raise ValueError('approved runtime mismatch')
    client=Client(base,cfg);histories={};last_heartbeat=-60;last_progress=None;last_stamp=None
    previous=read(folder/'recovery.json')
    if previous.get('boot_id')==boot_id():histories=previous.get('attempts',{})
    while not (folder/'STOP').exists():
        started=time.monotonic();training=read(root/'training-status.json');run=read(base/'data/control/run.json');deny=blocked(base,root)
        info=dict(pid=run.get('pid'),start=run.get('process_start'),boot_id=run.get('boot_id'))
        running=alive(info,'learning.accelerated_league',('--root',root))
        stamp=(training.get('round'),training.get('games'),training.get('phase'),training.get('operation_elapsed_seconds'))
        if running and stamp!=last_stamp:last_progress=time.time();last_stamp=stamp
        state='PAUSED' if deny=='administrator_paused' else 'RECOVERY_BLOCKED' if deny else 'RUNNING' if running else 'STARTING'
        health=dict(state=state,last_progress=last_progress,last_backup=last_backup(root),recovery_count=sum(len(h) for h in histories.values()))
        if started-last_heartbeat>=30:
            try:client.send('renew' if lease_valid(root,base) else 'acquire',run.get('run_id','unknown'),health);last_heartbeat=started
            except Exception as exc:health['network_error']=type(exc).__name__
        valid=lease_valid(root,base)
        if not valid:
            health['state']='LEASE_LOST'
            if running:os.kill(run['pid'],signal.SIGTERM)
        if read(base/'data/releases/active.json').get('root')!=str(root):deny='approved_runtime_changed';health['state']='RECOVERY_BLOCKED'
        for key,module,args in [('release','server.release_service',['--root',str(base/'data/releases')]),*[(lane,'server.dashboard_service',['--lane',lane,'--root',str(base/'data/dashboard'),'--db',str(base/'data/results.sqlite'),'--control-root',str(base/'data/control')]) for lane in ('control','collect','publish')]]:
            candidate=read(folder/(key+'.json'));history=histories.setdefault(key,[])
            if not alive(candidate,module,args):
                existing=find_running(module,args)
                if existing:
                    atomic(folder/(key+'.json'),existing);continue
                if restart_allowed(history,time.time()):
                    history.append(time.time());spawn(base,key,module,args)
                else:health.update(state='RECOVERY_BLOCKED',blocked_service=key)
        if valid and not deny and not running:
            history=histories.setdefault('learner',[])
            if restart_allowed(history,time.time()):
                history.append(time.time())
                try:
                    from .ppo_control import resume_if_needed
                    resume_if_needed(base/'data/control',base)
                except Exception as exc:health.update(state='RECOVERY_BLOCKED',recovery_error=type(exc).__name__)
            else:health.update(state='RECOVERY_BLOCKED',blocked_service='learner')
        atomic(folder/'recovery.json',dict(boot_id=boot_id(),attempts=histories))
        atomic(folder/'health.json',dict(health,updated_at=time.time(),lease_valid=valid))
        time.sleep(max(0,15-(time.monotonic()-started)))

def last_backup(root):
    proofs=[p.stat().st_mtime for p in (root/'archive-verified').glob('*.json') if read(p).get('full') and read(p).get('status')=='verified'];return max(proofs,default=None)

def bootstrap(base):
    cfg=read(base/'data/runtime/config.json')
    if not cfg:
        active=read(base/'data/releases/active.json')
        if active.get('root') and (Path(active['root'])/'current.json').exists():raise ValueError('runtime-continuity Apply required; existing checkpoint preserved')
        from .runtime_recovery import restore
        cfg=restore(base)
    if not cfg.get('monitor_url') or not Path(cfg.get('key_file','/nonexistent')).is_file():raise ValueError('monitor configuration required; learner was not started')
    folder=base/'data/runtime';folder.mkdir(exist_ok=True)
    with (folder/'bootstrap.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        info=read(folder/'supervisor.json')
        if alive(info,'server.runtime_supervisor',('--base',base,'serve')):return info
        return spawn(base,'supervisor','server.runtime_supervisor',['--base',str(base),'serve'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,default=BASE);p.add_argument('action',choices=['bootstrap','serve','check']);a=p.parse_args();base=a.base.resolve()
    if a.action=='serve':supervise(base)
    elif a.action=='bootstrap':print(bootstrap(base))
    else:print(json.dumps(dict(configured=bool(read(base/'data/runtime/config.json')),health=read(base/'data/runtime/health.json'))))
