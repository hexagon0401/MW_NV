"""Collector/publication/control lanes; reads public aggregates and private typed commands."""
import argparse,json,os,sqlite3,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
from cloud.supabase_storage import PrivateStorage
from .telemetry import atomic,activities,Resources,process_start
from .dashboard_data import sample,publish
from . import ppo_control

BASE=Path(__file__).resolve().parents[1]
TRAIN_KEYS=('status','phase','updated_at','games','round','policy_steps','completed_steps','sim_speed','workers','cpu_budget','adaptation_reason','learners','decision_seconds','teacher_seconds','rules_version','map_id','map_version','run_id','control_version','backup','pause_reason')
TEACHER_KEYS=('paired','skipped','requests','last_error','last_error_code','last_request_seconds','retry_in_seconds','async_inflight')
def training():
    try:d=json.loads(Path('data/training-status.json').read_text())
    except (OSError,ValueError):return {}
    if not d.get('run_id'):
        for base in ('data/league-v1','data/multi-mode-v1'):
            try:
                status=json.loads((Path(base)/'training-status.json').read_text())
                if status.get('updated_at')==d.get('updated_at'):d['run_id']=json.loads((Path(base)/'state.json').read_text()).get('run');break
            except (OSError,ValueError):pass
    result={k:d[k] for k in TRAIN_KEYS if k in d};result['teacher']={k:d.get('teacher',{}).get(k) for k in TEACHER_KEYS};result['publication']={k:d.get('publication',{}).get(k) for k in ('queued_archives','queued_replay')};return result

def pids():
    ids=set()
    for root in ('data/league-v1','data/multi-mode-v1'):
        for name in ('runner.pid','rollout.pid','initial-evaluation.pid','io-jobs/publish.pid','io-jobs/archive.pid'):
            try:
                pid=int((Path(root)/name).read_text());args=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
                if any(a.startswith((b'learning.',b'server.')) for a in args):ids.add(pid)
            except (OSError,ValueError):pass
    try:
        rows=[tuple(map(int,line.split())) for line in subprocess.check_output(['ps','-eo','pid=,ppid='],text=True).splitlines()]
        for _ in range(4):ids.update(pid for pid,parent in rows if parent in ids)
    except (OSError,ValueError):pass
    return ids

def collect(db,root,resource):
    t=training();rows=activities(os.environ.get('MW_NV_ACTIVITY_ROOT','data/activity'));known=Path(os.environ.get('MW_NV_ACTIVITY_ROOT','data/activity')).exists();running=[r for r in rows if r['state']=='RUNNING'];uncertain=any(r['state']=='STALE' for r in rows);counts={role:sum(r['role']==role for r in running) if known and not any(x['role']==role and x['state']=='STALE' for x in rows) else None for role in ('training','evaluation','diagnostic')}
    usage=resource.sample(pids());sample(db,dict(usage,sim_speed=t.get('sim_speed'),workers=t.get('workers')))
    snapshot=dict(updated_at=datetime.now(timezone.utc).isoformat(),training=t,resources=usage,activities=rows,activity=dict(running=len(running) if known and not uncertain else None,parked=sum(r['state']!='RUNNING' for r in rows) if known else None,**counts),activity_available=known)
    atomic(Path(root)/'snapshot.json',snapshot);return snapshot

def control_poll(root,store):
    status=ppo_control.status(root,training());prefix='control/commands';body=json.dumps(dict(prefix=prefix,limit=100,offset=0,sortBy=dict(column='created_at',order='asc'))).encode()
    items=json.loads(store._request('object/list/'+store.bucket,'POST',body))
    for item in items:
        name=item.get('name','')
        if not name.endswith('.json') or '/' in name:continue
        path=prefix+'/'+name
        command=json.loads(store._request('object/authenticated/'+store.bucket+'/'+path))
        ack=ppo_control.apply(root,command,status.get('run_id'))
        if ack['status']=='accepted' and command['action']=='resume_ppo':
            try:ppo_control.resume_if_needed(root,BASE)
            except (OSError,ValueError) as exc:ack.update(status='blocked',reason=type(exc).__name__)
        with sqlite3.connect(Path(root)/'control.sqlite') as conn:conn.execute('UPDATE commands SET ack=? WHERE id=?',(json.dumps(ack),command.get('request_id')))
        store._request('object/'+store.bucket+'/control/acks/'+name,'PUT',json.dumps(ack).encode())
        store._request('object/'+store.bucket,'DELETE',json.dumps(dict(prefixes=[path])).encode())
    status=ppo_control.status(root,training());store._request('object/'+store.bucket+'/control/status.json','PUT',json.dumps(status).encode());atomic(Path(root)/'status.json',status)

def run(lane,root='data/dashboard',db='data/results.sqlite',control_root='data/control'):
    import fcntl
    root=Path(root);root.mkdir(parents=True,exist_ok=True);lock=(root/(lane+'.lock')).open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:return
    atomic(root/(lane+'.pid.json'),dict(pid=os.getpid(),start=process_start(os.getpid())))
    resource=Resources();store=None
    while not (root/'STOP').exists():
        started=time.monotonic()
        try:
            if lane=='collect':collect(db,root,resource)
            else:
                if store is None:store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY'])
                if lane=='publish':publish(db,json.loads((root/'snapshot.json').read_text()),store,root/'cache')
                else:control_poll(control_root,store)
            atomic(root/(lane+'-status.json'),dict(status='ok',last_success=time.time()))
        except Exception as exc:atomic(root/(lane+'-status.json'),dict(status='retry',error=type(exc).__name__,updated_at=time.time()))
        delay=5 if lane=='control' else 30 if lane=='collect' else 60
        while time.monotonic()-started<delay and not (root/'STOP').exists():time.sleep(1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--lane',choices=['collect','publish','control'],required=True);p.add_argument('--root',default='data/dashboard');p.add_argument('--db',default='data/results.sqlite');p.add_argument('--control-root',default='data/control');a=p.parse_args();run(a.lane,a.root,a.db,a.control_root)
