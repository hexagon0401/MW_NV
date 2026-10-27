"""Release observer, private command queue and public sanitized publication."""
import argparse,fcntl,gzip,hashlib,json,os,subprocess,sys,time
from pathlib import Path
import yaml
from cloud.supabase_storage import PrivateStorage
from .releases import Registry,digest
from .release_observations import observe,read
from .telemetry import atomic,process_start

BASE=Path(__file__).resolve().parents[1]


def definitions(registry,base=BASE):
    blueprint=yaml.safe_load((base/'config/releases.yaml').read_text())
    folder=registry.root/'definitions';folder.mkdir(exist_ok=True)
    for row in blueprint['releases']:
        path=folder/(row['id']+'.json');saved=read(path)
        # Keep the artifact immutable across unrelated repository/UI changes.
        if saved and saved['spec']['revision']>=row['revision']:
            registry.register(saved['spec']);continue
        spec=dict(row);paths={}
        if row['id']=='mixed-maps':
            validation=base/'data/mission-normalization-v2';pilot=registry.root/'candidates/mixed-maps'/str(row['revision'])
            paths=dict(validation=str(validation),pilot=str(pilot),activity=str(base/'data/activity'),legacy=str(base/'data/league-v1'),runtime=str(registry.root/'artifacts/mixed-maps'/str(row['revision'])/'runtime'))
            spec['artifact']=dict(row['artifact'],runtime_digest=read(validation/'validation-code.json').get('sha256'),policy_sources={str(p.relative_to(validation)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('migrated','migration-sources') for p in (validation/folder).glob('ppo*') if p.suffix in ('.zip','.npz')})
        atomic(path,dict(spec=spec,paths=paths));registry.register(spec)


def refresh(registry):
    for item in registry.all():
        definition=read(registry.root/'definitions'/(item['id']+'.json'))
        if not definition:continue
        registry.observe(item['id'],observe(definition['spec'],definition['paths'],item['content_digest']))


def publish(registry,store):
    cache=read(registry.root/'publish-cache.json');known=set(cache.get('objects',[]));paths=set();items=[]
    for row in registry.all():
        id=row['id'];row['events']=[];events=registry.events(id,limit=200)
        # All historical pages stay immutable and are reused, never upload raw logs.
        with registry.db() as c:total=c.execute('SELECT count(*) FROM events WHERE release_id=?',(id,)).fetchone()[0]
        pages=[]
        for offset in range(0,total,200):
            with registry.db() as c:rs=c.execute('SELECT seq,at,code,data FROM events WHERE release_id=? ORDER BY seq LIMIT 200 OFFSET ?',(id,offset)).fetchall()
            data=[dict(seq=r['seq'],at=r['at'],code=r['code'],data=json.loads(r['data'])) for r in rs];body=json.dumps(data,separators=(',',':')).encode();sha=hashlib.sha256(body).hexdigest();path=f'releases/events/{id}/{sha}.json.gz';paths.add(path)
            if path not in known:store._request('object/'+store.bucket+'/'+path,'PUT',gzip.compress(body,mtime=0))
            pages.append(dict(path=path,first=data[0]['seq'],last=data[-1]['seq']))
        row['event_pages']=pages;row['event_count']=total;items.append(row)
    priority={'APPLYING':0,'READY':1,'VALIDATING':2,'BLOCKED':3,'FAILED':4,'PLANNED':5,'APPLIED':6,'ROLLED_BACK':7}
    items.sort(key=lambda r:(priority.get(r['status'],99),r['id']))
    document=dict(schema=1,updated_at=time.time(),last_seen=time.time(),items=items,summary={k:sum(i['status'] in states for i in items) for k,states in [('preparing',('PLANNED','VALIDATING')),('ready',('READY',)),('attention',('BLOCKED','FAILED'))]})
    store._request('object/'+store.bucket+'/releases/index.json','PUT',json.dumps(document,separators=(',',':')).encode());atomic(registry.root/'snapshot.json',document);atomic(registry.root/'publish-cache.json',dict(objects=sorted(paths)))
    return document


def poll_commands(registry,store):
    items=json.loads(store._request('object/list/'+store.bucket,'POST',json.dumps(dict(prefix='releases/commands',limit=100,offset=0,sortBy=dict(column='created_at',order='asc'))).encode()))
    for item in items:
        name=item.get('name','')
        if not name.endswith('.json') or '/' in name:continue
        key='releases/commands/'+name
        payload=json.loads(store._request('object/authenticated/'+store.bucket+'/'+key))
        try:result=registry.command(payload)
        except (ValueError,KeyError):result=dict(request_id=payload.get('request_id'),status='rejected',reason='STALE_OR_INVALID_COMMAND')
        if payload.get('action')=='set_auto' and result.get('status')=='accepted':
            with registry.db() as c:latest=c.execute('SELECT id FROM intents WHERE release_id=?',(payload['release_id'],)).fetchone()
            if latest and latest['id']==payload['request_id']:store._request('object/'+store.bucket+'/releases/authorizations/'+payload['release_id']+'.json','PUT',json.dumps(payload).encode())
        result['request_fields']={k:payload.get(k) for k in ('request_id','release_id','content_digest','action','enabled')}
        store._request('object/'+store.bucket+'/releases/acks/'+name,'PUT',json.dumps(result).encode());store._request('object/'+store.bucket,'DELETE',json.dumps(dict(prefixes=[key])).encode())


def restore_authorizations(registry,store):
    for item in registry.all():
        try:
            payload=json.loads(store._request('object/authenticated/'+store.bucket+'/releases/authorizations/'+item['id']+'.json'))
            if payload.get('content_digest')==item['content_digest']:registry.command(payload)
        except (OSError,ValueError,KeyError):pass


def maybe_pilot(registry):
    from .release_artifacts import capture
    for item in registry.all():
        if item['id']!='mixed-maps' or item['status'] in ('APPLYING','APPLIED','ROLLED_BACK','READY'):continue
        definition_path=registry.root/'definitions'/(item['id']+'.json');definition=read(definition_path);paths=definition['paths'];validation=read(Path(paths['validation'])/'rollout-status.json')
        if validation.get('stage')!='candidate_validated' or validation.get('status')!='validated':continue
        pilot=Path(paths['pilot']);pidinfo=read(pilot/'pilot.pid.json')
        if pidinfo.get('pid') and process_start(pidinfo['pid'])==pidinfo.get('start'):
            cmd=Path(f"/proc/{pidinfo['pid']}/cmdline")
            if cmd.exists() and b'learning.release_pilot' in cmd.read_bytes().split(b'\0'):continue
        state=read(pilot/'state.json');status=read(pilot/'pilot-status.json')
        if state.get('pause_reason') or status.get('status')=='COMPLETE':continue
        if status.get('status')=='STARTING' and time.time()-status.get('updated_at',0)<60:continue
        if status.get('status')=='WAITING_ARCHIVE' and time.time()-status.get('updated_at',0)<60:continue
        capture(BASE,paths['runtime'],definition['spec']['artifact']['runtime_digest']);pilot.mkdir(parents=True,exist_ok=True)
        atomic(Path(paths['validation'])/'release-staging.json',dict(pilot=str(pilot.resolve()),runtime=paths['runtime']))
        atomic(pilot/'pilot-status.json',dict(status='STARTING',updated_at=time.time()))
        with (pilot/'orchestrator.log').open('ab') as log:
            process=subprocess.Popen([sys.executable,'-u','-m','learning.release_pilot','--definition',str(definition_path.resolve()),'--registry-root',str(registry.root.resolve()),'--base',str(BASE)],stdout=log,stderr=log,stdin=subprocess.DEVNULL,start_new_session=True)
        atomic(pilot/'pilot.pid.json',dict(pid=process.pid,start=process_start(process.pid)))


def run(root):
    registry=Registry(root);lock=(registry.root/'agent.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);atomic(registry.root/'agent.json',dict(pid=os.getpid(),start=process_start(os.getpid())))
    definitions(registry);store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY']);restore_authorizations(registry,store);last=0.;worker=None
    while not (registry.root/'STOP').exists():
        try:
            refresh(registry);poll_commands(registry,store);maybe_pilot(registry)
            worker_info=read(registry.root/'apply-worker.json')
            worker_alive=False
            if worker_info.get('pid') and process_start(worker_info['pid'])==worker_info.get('start'):
                try:worker_alive=b'server.release_apply' in Path(f"/proc/{worker_info['pid']}/cmdline").read_bytes().split(b'\0')
                except OSError:pass
            if not worker_alive:
                pending=registry.pending()
                if not pending:registry.auto_request();pending=registry.pending()
                if pending and (pending['phase']!='RECOVERY_REQUIRED' or time.time()-pending['updated']>=60):
                    with (registry.root/'apply.log').open('ab') as log:worker=subprocess.Popen([sys.executable,'-u','-m','server.release_apply','--root',str(registry.root.resolve())],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
                    atomic(registry.root/'apply-worker.json',dict(pid=worker.pid,start=process_start(worker.pid)))
            if time.monotonic()-last>=15:publish(registry,store);last=time.monotonic()
            atomic(registry.root/'agent-status.json',dict(status='ok',last_seen=time.time()))
        except Exception as exc:atomic(registry.root/'agent-status.json',dict(status='retry',reason=type(exc).__name__,last_seen=time.time()))
        for _ in range(5):
            if (registry.root/'STOP').exists():break
            time.sleep(1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='data/releases');a=p.parse_args();run(a.root)
