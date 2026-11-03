"""Recover the separately fixed publisher without changing the running engine."""
import json,os,signal,subprocess,sys
from pathlib import Path
from .release_artifacts import verify
from .telemetry import process_start,atomic

def ensure(base):
    base=Path(base).resolve();path=base/'data/replay-publication-runtime.json'
    if not path.exists():return
    spec=json.loads(path.read_text())
    if not spec.get('root'):return
    root=Path(spec['root']).resolve();runtime=Path(spec['runtime']).resolve()
    run=json.loads((base/'data/control/run.json').read_text())
    if Path(run['root']).resolve()!=root:return
    if not root.is_relative_to(base/'data') or not runtime.is_relative_to(base/'data/releases/artifacts'):raise ValueError('unregistered publisher')
    verify(runtime,spec['sha256'])
    folder=root/'io-jobs';pidfile=folder/'publish.pid'
    try:
        pid=int(pidfile.read_text());args=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        owned=b'learning.background_io' in args and str(root).encode() in args and b'publish' in args
        managed_path=folder/'publisher-override.json'
        managed=json.loads(managed_path.read_text()) if managed_path.exists() else {}
        if owned and managed.get('pid')==pid and managed.get('start')==process_start(pid) and managed.get('runtime')==str(runtime):return
        if owned:os.kill(pid,signal.SIGTERM)
    except (OSError,ValueError):pass
    env=dict(os.environ,PYTHONPATH=str(runtime),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLCONFIGDIR='/tmp/mw-mpl')
    with (folder/'publish.log').open('ab') as log:
        p=subprocess.Popen([sys.executable,'-u','-m','learning.background_io','--root',str(root),'--lane','publish'],cwd=runtime,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
    pidfile.write_text(str(p.pid))
    atomic(folder/'publisher-override.json',dict(pid=p.pid,start=process_start(p.pid),runtime=str(runtime)))
