"""Durable bounded latest publications and immutable archive jobs, outside simulation."""
import json,os,pickle,shutil,subprocess,sys,time,uuid
from pathlib import Path

def latest(root,kind,value):
    folder=Path(root)/'io-jobs';folder.mkdir(parents=True,exist_ok=True)
    target=folder/(kind+('.pkl' if kind=='replay' else '.json'));temp=target.with_name(target.name+'.'+uuid.uuid4().hex+'.partial')
    if kind=='replay':
        engine,initial,metadata=value;metadata=dict(metadata or {});metadata.setdefault('completed_at',time.time());value=(engine,initial,metadata)
        with temp.open('wb') as f:pickle.dump(value,f,protocol=5)
    else:temp.write_text(json.dumps(value))
    temp.replace(target)

def archive(root,checkpoint,state,full):
    root=Path(root);folder=root/'io-jobs'/'archives';folder.mkdir(parents=True,exist_ok=True)
    disk_guard(root)
    temp=folder/('.'+uuid.uuid4().hex);temp.mkdir();shutil.copytree(checkpoint,temp/'checkpoint')

    if full:
        for name in ('baseline','opponents'):
            if (root/name).exists():shutil.copytree(root/name,temp/name)
        step=96 if state.get('contract') in ('tactics-3','tactics-4','tactics-5') else 50
        milestone=state['completed_games']//step*step
        for name in sorted({'games-00000000',f'games-{state["completed_games"]:08d}',f'games-{milestone:08d}'}):
            src=root/'evaluations'/name
            if src.exists():shutil.copytree(src,temp/'evaluations'/name,dirs_exist_ok=True)
    (temp/'job.json').write_text(json.dumps(dict(state=state,full=full)))
    temp.rename(folder/temp.name[1:])

def disk_guard(root):
    root=Path(root)
    size=0
    for name in ('archive-pending','io-jobs/archives'):
        for p in (root/name).rglob('*'):
            try:
                if p.is_file():size+=p.stat().st_size
            except FileNotFoundError:pass
    if shutil.disk_usage(root).free<1024**3 or size>=2*1024**3:raise RuntimeError('ARCHIVE_DISK_LIMIT')

def start(root):
    root=Path(root).resolve();folder=root/'io-jobs';folder.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MW_NV_TORCH_THREADS='1')
    for lane in ('publish','archive'):
        pidfile=folder/(lane+'.pid')
        try:
            pid=int(pidfile.read_text());args=(Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0')
            if b'learning.background_io' in args and str(root).encode() in args and lane.encode() in args:continue
        except (OSError,ValueError):pass
        with (folder/(lane+'.log')).open('ab') as log:
            p=subprocess.Popen([sys.executable,'-u','-m','learning.background_io','--root',str(root),'--lane',lane],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
        pidfile.write_text(str(p.pid))

def process_latest(root,kind):
    folder=Path(root)/'io-jobs';path=folder/(kind+('.pkl' if kind=='replay' else '.json'));working=path.with_suffix(path.suffix+'.working')
    if path.exists():path.replace(working)
    elif not working.exists():return False
    if kind=='status':
        from cloud.supabase_storage import PrivateStorage
        store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY'])
        import fcntl
        Path('data').mkdir(exist_ok=True);pointer=Path('data/training-publication-pointer.json')
        with Path('data/training-publication.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            payload=working.read_bytes();timestamp=json.loads(payload).get('updated_at','')
            try:previous=json.loads(pointer.read_text()).get('updated_at','')
            except (OSError,ValueError):previous=''
            if not timestamp or timestamp>=previous:
                store._request('object/'+store.bucket+'/training-status.json','PUT',payload)
                if timestamp:
                    temp=pointer.with_suffix('.partial');temp.write_text(json.dumps(dict(updated_at=timestamp)));temp.replace(pointer)
    else:
        from .replay_sink import publish_latest
        with working.open('rb') as f:engine,initial,metadata=pickle.load(f)
        publish_latest(engine,initial,metadata)
    working.unlink();return True

def process_archives(root):
    from .league_archive import spool,publish_pending
    root=Path(root);folder=root/'io-jobs'/'archives'
    for job in sorted(folder.glob('*')):
        if job.name.startswith('.'):continue
        info=json.loads((job/'job.json').read_text())
        spool(root,job/'checkpoint',info['state'],info['full'],asset_root=job);shutil.rmtree(job)
    return publish_pending(root)

def run(root,lane):
    import fcntl
    root=Path(root);folder=root/'io-jobs';lock=(folder/(lane+'.lock')).open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:return
    retry=0.;stats_at=0.;last_db=None
    while not (folder/'STOP').exists():
        if time.monotonic()<retry:time.sleep(1);continue
        try:
            if lane=='archive':
                result=process_archives(root);retry=time.monotonic()+30
                if result['status']!='verified':raise OSError('archive verification deferred')
            else:
                process_latest(root,'status');process_latest(root,'replay')
                db=Path('data/results.sqlite');stamp=db.stat().st_mtime_ns if db.exists() else None
                if stamp!=last_db and time.monotonic()>=stats_at:
                    from .public_results import publish
                    publish();last_db=stamp;stats_at=time.monotonic()+60
            target=folder/(lane+'-status.json');temp=target.with_suffix('.partial');temp.write_text(json.dumps(dict(status='ok',last_success=time.time())));temp.replace(target)
        except Exception as exc:
            (folder/(lane+'-status.json')).write_text(json.dumps(dict(status='retry',error=type(exc).__name__,updated_at=time.time())))
            retry=time.monotonic()+30
        time.sleep(1)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--lane',choices=['publish','archive'],required=True);a=p.parse_args();run(a.root,a.lane)
