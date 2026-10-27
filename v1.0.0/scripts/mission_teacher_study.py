"""One-shot dependent study, not a recurring scheduler; leave PPO production isolated."""
import argparse,fcntl,hashlib,json,os,subprocess,sys,time
from collections import Counter
from pathlib import Path


def fingerprint(base):
    files=sorted(p for folder in ('engine','agents','learning','config','server') for p in (base/folder).glob('*') if p.suffix in ('.py','.yaml'))
    return hashlib.sha256(b''.join(str(p.relative_to(base)).encode()+p.read_bytes() for p in files)).hexdigest()


def ready(base,audit):
    try:
        report=json.loads((audit/'engine-audit.json').read_text());pin=json.loads((audit/'validation-code.json').read_text())
        return report.get('complete') is True and len(report.get('results',[]))==30 and Counter(r.get('scenario_id') for r in report['results'])=={'2':10,'3':10,'4':10} and all(r.get('replay_hash_verified') for r in report['results']) and pin.get('sha256')==fingerprint(base)
    except (OSError,ValueError,KeyError):return False


def pilot_ready(root):
    try:
        state=json.loads((root/'state.json').read_text());report=state.get('pilot_report',{})
        return state.get('completed_games',0)>=192 and bool(report) and not report.get('pause',True)
    except (OSError,ValueError):return False


def run(base,audit,root,updates=128):
    root.mkdir(parents=True,exist_ok=True);lock=(root/'study.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    def status(phase,**extra):
        p=root/'status.json';temp=p.with_suffix('.partial');temp.write_text(json.dumps(dict(phase=phase,pid=os.getpid(),updated_at=time.time(),updates=updates,**extra)));temp.replace(p)
    os.nice(15)
    while not ready(base,audit) or not pilot_ready(audit):status('WAITING_MIXED_PILOT');time.sleep(30)
    source=audit/'migrated';status('RUNNING_COMPARISON')
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MW_NV_TORCH_THREADS='1',MPLCONFIGDIR='/tmp/mw-mpl',MW_NV_ACTIVITY_ROOT=str(root/'activity'),MW_NV_PUBLISH_TRAINING='0')
    result=subprocess.run([sys.executable,'-u','-m','learning.teacher_comparison','--root',str(root),'--source',str(source),'--updates',str(updates)],cwd=base,env=env)
    status('COMPLETED' if result.returncode==0 else 'FAILED',returncode=result.returncode,strategic_improvement_established=False)

if __name__=='__main__':
    base=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--audit-root',default='data/mission-normalization-v2');p.add_argument('--root',default='data/teacher-ablation-v2');p.add_argument('--updates',type=int,default=128);a=p.parse_args();run(base,(base/a.audit_root).resolve(),(base/a.root).resolve(),a.updates)
