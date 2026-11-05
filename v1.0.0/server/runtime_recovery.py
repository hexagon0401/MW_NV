"""Immutable executable code + verified full-checkpoint discovery for a fresh workspace."""
import hashlib,json,os,tarfile,tempfile,re
from pathlib import Path
from .release_artifacts import verify,fingerprint,FOLDERS
from .telemetry import atomic
from .release_observations import read

def pack_code(runtime,destination):
    runtime=Path(runtime);verify(runtime,fingerprint(runtime));destination=Path(destination)
    import gzip
    paths=[p for folder in FOLDERS for p in (runtime/folder).rglob('*') if p.is_file() and not p.is_symlink()]
    if any(p.name.startswith('.env') or p.suffix in ('.key','.pem') for p in paths):raise ValueError('credentials forbidden in code archive')
    paths += [runtime/name for name in ('artifact-files.json','requirements.lock','requirements.txt','pyproject.toml') if (runtime/name).is_file()]
    with destination.open('wb') as output,gzip.GzipFile(fileobj=output,mode='wb',mtime=0,filename='') as packed,tarfile.open(fileobj=packed,mode='w') as tar:
        for path in sorted(paths):
            info=tar.gettarinfo(path,arcname=str(path.relative_to(runtime)));info.mtime=0;info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o644
            with path.open('rb') as source:tar.addfile(info,source)
    return hashlib.sha256(destination.read_bytes()).hexdigest()

def unpack_code(archive,destination,sha,runtime_digest):
    archive=Path(archive);destination=Path(destination)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=sha:raise ValueError('runtime archive checksum')
    with tarfile.open(archive) as tar:
        entries=tar.getmembers()
        if len(entries)>5000 or sum(e.size for e in entries)>64*1024**2:raise ValueError('runtime archive limit')
        for e in entries:
            name=Path(e.name)
            if not e.isfile() or name.is_absolute() or '..' in name.parts or name.name.startswith('.env') or name.suffix in ('.key','.pem') or (name.parts[0] not in FOLDERS and e.name not in ('artifact-files.json','requirements.lock','requirements.txt','pyproject.toml')):raise ValueError('runtime archive path')
        destination.mkdir(parents=True,exist_ok=True);tar.extractall(destination,filter='data')
    verify(destination,runtime_digest)

def validate_transport(proof,limit=512*1024**2):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}',proof.get('release','')):raise ValueError('invalid archive release')
    transport=proof['transport'];asset=transport.get('asset','');chunks=transport.get('chunks',[])
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,200}',asset) or not 1<=len(chunks)<=1024:raise ValueError('invalid archive transport')
    if proof.get('sha256')!=transport.get('sha256') or not re.fullmatch('[a-f0-9]{64}',proof['sha256']):raise ValueError('invalid archive checksum')
    size=0
    for i,c in enumerate(chunks):
        if c.get('name')!=asset+f'.part{i:03d}' or type(c.get('size')) is not int or not 1<=c['size']<=524288 or not re.fullmatch('[a-f0-9]{64}',c.get('sha256','')):raise ValueError('invalid archive chunk')
        size+=c['size']
    if size>limit:raise ValueError('archive transport limit')

def upload_code(base,runtime):
    from learning.league_archive import gh,transfer,download,REPO
    base=Path(base);runtime=Path(runtime);digest=fingerprint(runtime);tag='runtime-code-'+digest[:16]
    try:release=json.loads(gh('api',f'repos/{REPO}/releases/tags/{tag}'))
    except RuntimeError:
        gh('release','create',tag,'--repo',REPO,'--target','dev/v1.0.0','--title',tag,'--notes','Immutable runtime source; no credentials or model files.','--latest=false');release={'assets':[]}
    with tempfile.TemporaryDirectory() as temp:
        archive=Path(temp)/'runtime.tar.gz';sha=pack_code(runtime,archive)
        transport=transfer(archive,tag,sha,release.get('assets',[]))
        with tempfile.TemporaryDirectory() as downloaded:
            received=download(tag,transport,downloaded);unpack_code(received,Path(downloaded)/'verified',sha,digest)
    proof=dict(release=tag,transport=transport,sha256=sha,runtime_digest=digest,verified=True)
    atomic(base/'data/runtime/code-proof.json',proof);return proof

def publish_pointer(root,proof,base=None):
    if not proof.get('full') or proof.get('status')!='verified':return
    base=Path(base or os.environ.get('MW_NV_INSTALLATION_BASE',Path(__file__).resolve().parents[1]));cfg=read(base/'data/runtime/config.json');code=read(base/'data/runtime/code-proof.json')
    if not code.get('verified') or code.get('runtime_digest')!=cfg.get('runtime_digest') or Path(cfg.get('root','/missing')).resolve()!=Path(root).resolve():return
    from cloud.supabase_storage import PrivateStorage
    store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY'])
    registrations=[]
    from .releases import Registry
    registry=Registry(base/'data/releases')
    for item in registry.all():
        registrations.append(dict(definition=read(registry.root/'definitions'/(item['id']+'.json')),state=item))
    data=dict(schema=1,source_base=str(base.resolve()),registrations=registrations,root=str(Path(root).resolve().relative_to(base.resolve())),code=code,checkpoint=proof,monitor_url=cfg['monitor_url'],release_id=cfg['release_id'])
    store._request('object/'+store.bucket+'/runtime/recovery.json','PUT',json.dumps(data).encode())

def restore(base):
    from cloud.supabase_storage import PrivateStorage
    from learning.league_archive import download,restore_bundle,verify as verify_checkpoint
    from .runtime_lease import Client,lease_valid
    import threading,time
    base=Path(base).resolve();key=os.environ.get('MW_NV_RUNTIME_MONITOR_KEY')
    if not key or len(key)<32:raise ValueError('MW_NV_RUNTIME_MONITOR_KEY required for fresh restore')
    store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY']);d=json.loads(store._request('object/authenticated/'+store.bucket+'/runtime/recovery.json'))
    if d.get('schema')!=1 or not d['checkpoint'].get('full') or d['checkpoint'].get('status')!='verified':raise ValueError('verified full recovery required')
    validate_transport(d['code'],64*1024**2);validate_transport(d['checkpoint'])
    root=(base/d['root']).resolve()
    if not root.is_relative_to(base/'data/releases/production') or (root/'current.json').exists():raise ValueError('restore must not overwrite local checkpoint')
    runtime=base/'data/releases/artifacts/runtime-restored'/d['code']['runtime_digest']/'runtime'
    keyfile=base/'data/runtime/monitor.key';keyfile.parent.mkdir(parents=True,exist_ok=True);keyfile.write_text(key);keyfile.chmod(0o600)
    cfg=dict(root=str(root),runtime=str(runtime),runtime_digest=d['code']['runtime_digest'],monitor_url=d['monitor_url'],key_file=str(keyfile),release_id=d['release_id'])
    client=Client(base,cfg);client.send('acquire',d['checkpoint']['run'],dict(state='RESTORING'));finished=threading.Event()
    def heartbeat():
        while not finished.wait(30):
            try:client.send('renew',d['checkpoint']['run'],dict(state='RESTORING'))
            except Exception:pass
    thread=threading.Thread(target=heartbeat,daemon=True);thread.start()
    try:
        with tempfile.TemporaryDirectory() as temp:
            code=download(d['code']['release'],d['code']['transport'],temp);unpack_code(code,runtime,d['code']['sha256'],d['code']['runtime_digest'])
        with tempfile.TemporaryDirectory() as temp:
            archive=download(d['checkpoint']['release'],d['checkpoint']['transport'],temp);verify_checkpoint(archive,d['checkpoint']['sha256'],True);restore_bundle(archive,root,d['checkpoint']['sha256'])
        if not lease_valid(root,base):raise ValueError('lease lost during restore')
        state=read(root/'state.json');atomic(root/'validation-gates.json',dict(approved_for_pilot=True,code_sha256=cfg['runtime_digest'],restored=True))
        atomic(base/'data/releases/active.json',dict(root=str(root),runtime=str(runtime),release_id=cfg['release_id'],revision=1))
        atomic(base/'data/control/run.json',dict(root=str(root),source=str(root/'baseline'),kind='mission',pilot=state['pilot'],run_id=state['run'],pid=0,process_start=None))
        atomic(base/'data/control/state.json',dict(desired=state.get('control_desired','paused'),version=0,enabled=True))
        # Restore trusted private release registrations, rebasing paths for the new workspace.
        from .releases import Registry
        registry=Registry(base/'data/releases');old_base=d.get('source_base','')
        for entry in d.get('registrations',[]):
            definition=entry['definition'];spec=definition['spec'];paths=definition.get('paths',{})
            paths={k:(str(base/v[len(old_base)+1:]) if isinstance(v,str) and old_base and v.startswith(old_base+'/') else v) for k,v in paths.items()}
            if spec['id']==cfg['release_id']:paths['runtime']=str(runtime)
            atomic(registry.root/'definitions'/(spec['id']+'.json'),dict(spec=spec,paths=paths));registry.register(spec)
            if entry['state'].get('status') in ('APPLIED','ROLLED_BACK'):
                with registry.db() as conn:conn.execute('UPDATE releases SET state=? WHERE id=?',(json.dumps({k:v for k,v in entry['state'].items() if k in ('status','steps','blockers','connection')}),spec['id']))
        atomic(base/'data/runtime/code-proof.json',d['code']);atomic(base/'data/runtime/config.json',cfg)
    finally:finished.set();thread.join()
    return cfg
