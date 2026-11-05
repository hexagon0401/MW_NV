"""One isolated, resumable192-game candidate pilot; never registers production control."""
import argparse,fcntl,json,os,subprocess,sys,time
from pathlib import Path
from server.telemetry import atomic,process_start
from server.release_artifacts import sandbox
from .adaptive_resources import resources


def run(definition,registry_root,base):
    spec=definition['spec'];paths=definition['paths'];root=Path(paths['pilot']);root.mkdir(parents=True,exist_ok=True);lock=(root/'pilot.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    atomic(root/'pilot.pid.json',dict(pid=os.getpid(),start=process_start(os.getpid())))
    reservation=Path(base)/'data/releases/reservation.json'
    try:
        while True:
            atomic(reservation,dict(pid=os.getpid(),start=process_start(os.getpid()),cores=2,updated_at=time.time()))
            r=resources()
            try:production=json.loads((Path(paths['legacy'])/'training-status.json').read_text())
            except (OSError,ValueError):production={}
            if r['cpu_budget']>=4 and r['memory_free_fraction']>=.2 and r['cpu_pressure']<=10 and production.get('workers',0)<=1:break
            atomic(root/'pilot-status.json',dict(status='WAITING_RESOURCES',updated_at=time.time()));time.sleep(15)
        cwd=sandbox(paths['runtime'],root/'sandbox',base);gate=json.loads((Path(paths['validation'])/'validation-gates.json').read_text());atomic(root/'validation-gates.json',gate)
        env=dict(os.environ,PYTHONPATH=paths['runtime'],MW_NV_PUBLISH_TRAINING='0',MW_NV_ASYNC_IO='1',MW_NV_SERIAL_INITIAL_EVALUATION='1',MW_NV_RELEASE_PILOT='1',MW_NV_CONTROL_ROOT=str(cwd/'data/control'),MW_NV_ACTIVITY_ROOT=str(cwd/'data/activity'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MW_NV_TORCH_THREADS='1',MPLCONFIGDIR='/tmp/mw-mpl')
        # A broker is shared, but statuses, ledger, jobs, control and activity are isolated.
        atomic(root/'pilot-status.json',dict(status='RUNNING',updated_at=time.time()))
        command=[sys.executable,'-u','-m','learning.accelerated_league','--kind','mission','--root',str(root.resolve()),'--source',str((Path(paths['validation'])/'migrated').resolve()),'--pilot','192','--workers','1','--stop-after-pilot']
        state=json.loads((root/'state.json').read_text()) if (root/'state.json').exists() else {}
        if state.get('completed_games',0)<192:
            saved=json.loads((root/'child.json').read_text()) if (root/'child.json').exists() else {}
            def alive_saved():
                try:return process_start(saved['pid'])==saved['start'] and b'learning.accelerated_league' in Path(f"/proc/{saved['pid']}/cmdline").read_bytes().split(b'\0')
                except (OSError,KeyError):return False
            child=None
            if not alive_saved():
                child=subprocess.Popen(command,cwd=cwd,env=env);saved=dict(pid=child.pid,start=process_start(child.pid));atomic(root/'child.json',saved)
            pressured_since=None
            while alive_saved():
                r=resources();pressured=r['memory_free_fraction']<.2 or r['cpu_pressure']>10
                pressured_since=pressured_since or time.monotonic() if pressured else None
                if pressured_since is not None and time.monotonic()-pressured_since>=30:atomic(root/'resource-pause.json',dict(paused=True,reason='RESOURCE_BUDGET'))
                elif not pressured:(root/'resource-pause.json').unlink(missing_ok=True)
                atomic(reservation,dict(pid=os.getpid(),start=process_start(os.getpid()),cores=2,updated_at=time.time()));time.sleep(5)
            if child is not None and child.wait():raise RuntimeError('candidate pilot failed')
        state=json.loads((root/'state.json').read_text())
        if state['completed_games']<192 or state.get('pilot_report',{}).get('pause',True):raise ValueError('candidate pilot incomplete or regressing')
        # Final exact generation is archived before Ready; sandbox ledger stays private.
        from .league_archive import spool,publish_pending
        old=Path.cwd()
        try:
            os.chdir(cwd);checkpoint=root/json.loads((root/'current.json').read_text())['path'];spool(root,checkpoint,state,True);result=publish_pending(root)
        finally:os.chdir(old)
        atomic(root/'pilot-status.json',dict(status='COMPLETE' if result['status']=='verified' else 'WAITING_ARCHIVE',updated_at=time.time()))
    finally:
        try:
            d=json.loads(reservation.read_text())
            if d.get('pid')==os.getpid():reservation.unlink()
        except (OSError,ValueError):pass

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--definition',required=True);p.add_argument('--registry-root',required=True);p.add_argument('--base',required=True);a=p.parse_args();run(json.loads(Path(a.definition).read_text()),a.registry_root,a.base)
