"""Fixed operational handlers; trusted local definitions supply immutable artifacts."""
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
from .telemetry import atomic,process_start
from .release_observations import read
from .release_artifacts import fingerprint

BASE=Path(__file__).resolve().parents[1]
# Frozen runtime paths may be under data/releases; retain the installation base explicitly.
BASE=Path(os.environ.get('MW_NV_INSTALLATION_BASE',BASE)).resolve()


def owned(pid,module,root=None,start=None):
    try:
        args=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        same_root=root is None
        if root is not None and b'--root' in args:
            value=Path(args[args.index(b'--root')+1].decode())
            actual=value if value.is_absolute() else Path(f'/proc/{pid}/cwd').resolve()/value
            same_root=actual.resolve()==Path(root).resolve()
        return module.encode() in args and same_root and (start is None or process_start(pid)==start)
    except (OSError,ValueError,IndexError,UnicodeError):return False


def alive_run(root):
    try:pid=int((Path(root)/'runner.pid').read_text());return owned(pid,'learning.accelerated_league',root)
    except (OSError,ValueError):return False


def stop_run(root,marker,notify):
    root=Path(root);flag=root/'STOP'
    if flag.exists() and flag.read_text()!=marker:raise ValueError('run already stopped by another owner')
    atomic(root/'release-stop-owner.json',dict(marker=marker));flag.write_text(marker)
    deadline=time.monotonic()+1800
    while alive_run(root):
        if time.monotonic()>deadline:raise TimeoutError('safe checkpoint boundary timeout')
        notify(waiting_for_checkpoint=True);time.sleep(5)


def exact_recovery(root):
    root=Path(root);pointer=read(root/'current.json');folder=root/pointer['path'];state=read(folder/'state.json')
    policies={f'ppo{i}.npz':hashlib.sha256((folder/f'ppo{i}.npz').read_bytes()).hexdigest() for i in (1,2)}
    for p in (root/'archive-verified').glob('*.json'):
        m=read(p)
        if m.get('full') and m.get('status')=='verified' and m.get('generation')==state['generation'] and m.get('policies')==policies:return m
    return None


def archive_exact(root):
    if exact_recovery(root):return exact_recovery(root)
    from learning.league_archive import spool,publish_pending
    root=Path(root);folder=root/read(root/'current.json')['path'];spool(root,folder,read(folder/'state.json'),True);publish_pending(root)
    proof=exact_recovery(root)
    if not proof:raise ValueError('exact recovery not remotely verified')
    return proof


def spawn(root,source,kind,pilot,cwd,desired,release_root,release_id):
    root=Path(root);env=dict(os.environ,MW_NV_INSTALLATION_BASE=str(BASE),MW_NV_PUBLISH_TRAINING='1',MW_NV_ASYNC_IO='1',MW_NV_CONTROL_ROOT=str(BASE/'data/control'),MW_NV_ACTIVITY_ROOT=str(BASE/'data/activity'),MW_NV_TORCH_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    for key in ('MW_NV_RELEASE_PILOT','MW_NV_SERIAL_INITIAL_EVALUATION','MW_NV_EXPERIMENT_SEED'):env.pop(key,None)
    env['PYTHONPATH']=str(cwd)
    state=read(root/'state.json')
    if state.get('contract')=='tactics-5':env.update(MW_NV_EXPLORATION='1',MW_NV_DISABLE_MISSION_COACH='1')
    else:env.pop('MW_NV_EXPLORATION',None)
    args=[str(BASE/'.venv/bin/python'),'-u','-m','learning.accelerated_league','--kind',kind,'--root',str(root.resolve()),'--source',str(Path(source).resolve()),'--pilot',str(pilot)]
    with (root/'release-runner.log').open('ab') as log:p=subprocess.Popen(args,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
    return p.pid


class MixedTraining:
    def __init__(self,definition,registry):self.definition=definition;self.paths=definition['paths'];self.spec=definition['spec'];self.registry=registry
    def validate(self):
        from .release_artifacts import verify
        verify(self.paths['runtime'],self.spec['artifact']['runtime_digest'])
        root=Path(self.paths['pilot']);state=read(root/'state.json')
        if state.get('completed_games',0)<192 or state.get('pilot_report',{}).get('pause',True) or not exact_recovery(root):raise ValueError('candidate not verified')
    def prepare(self,journal,notify):
        if 'old_run' not in journal:
            old=read(BASE/'data/control/run.json')
            if not old.get('root') or not old.get('source'):raise ValueError('operational source not registered')
            root=Path(old.get('root',self.paths['legacy'])).resolve()
            if not root.is_relative_to(BASE/'data'):raise ValueError('unregistered operational root')
            pid=old.get('pid');cwd=Path(f'/proc/{pid}/cwd').resolve() if pid and owned(pid,'learning.accelerated_league') else BASE
            if cwd==BASE:
                from .release_artifacts import capture
                sha=fingerprint(BASE);cwd=capture(BASE,self.registry.root.resolve()/'artifacts/legacy'/sha/'runtime',sha)
                atomic(self.registry.root/'legacy-runtime.json',dict(root=str(root),runtime=str(cwd)))
            if cwd!=BASE and not cwd.is_relative_to(self.registry.root.resolve()/'artifacts'):raise ValueError('unregistered runtime')
            notify(old_run=dict(root=str(root),source=old.get('source'),kind=old.get('kind','legacy'),pilot=old.get('pilot',200),cwd=str(cwd)),old_active=read(self.registry.root/'active.json'))
            journal.update(old_run=dict(root=str(root),source=old.get('source'),kind=old.get('kind','legacy'),pilot=old.get('pilot',200),cwd=str(cwd)))
        marker='release:'+self.spec['id']+':'+str(self.spec['revision'])+'\n';notify(stop_marker=marker)
        stop_run(journal['old_run']['root'],marker,notify);proof=archive_exact(journal['old_run']['root']);notify(old_recovery=proof)
        candidate=exact_recovery(self.paths['pilot'])
        if not candidate:raise ValueError('candidate source changed')
        notify(candidate_recovery=candidate,new_root=str(self.registry.root.resolve()/'production'/self.spec['id']/str(self.spec['revision'])))
    def switch(self,journal,notify):
        from learning.league_archive import download,restore_bundle
        import tempfile
        root=Path(journal['new_root'])
        if root.exists() and read(root/'state.json').get('release_id')!=self.spec['id']:raise ValueError('operational destination belongs to another release')
        if not root.exists():
            temporary=root.with_name(root.name+'.partial');shutil.rmtree(temporary,ignore_errors=True);temporary.parent.mkdir(parents=True,exist_ok=True)
            proof=journal['candidate_recovery']
            with tempfile.TemporaryDirectory() as tmp:
                bundle=download(proof['release'],proof['transport'],tmp);restore_bundle(bundle,temporary,proof['sha256'])
            # Candidate ledger is preserved privately, never merged into production.
            (temporary/'results.sqlite').unlink(missing_ok=True)
            folder=temporary/read(temporary/'current.json')['path'];state=read(folder/'state.json');state.update(run=state['run']+'-release-'+self.spec['id']+'-'+str(self.spec['revision']),operational_start_games=state['completed_games'],release_id=self.spec['id'],release_revision=self.spec['revision'])
            from .ppo_control import state as control_state
            state['control_desired']=control_state(BASE/'data/control')['desired'];atomic(folder/'state.json',state);atomic(temporary/'state.json',state);temporary.rename(root)
        notify(new_root=str(root))
        atomic(self.registry.root/'active.json',dict(release_id=self.spec['id'],revision=self.spec['revision'],root=str(root),runtime=self.paths['runtime']))
        if not alive_run(root):
            (root/'STOP').unlink(missing_ok=True)
            pid=spawn(root,root/'baseline','mission',192,Path(self.paths['runtime']),None,self.registry.root,self.spec['id']);notify(new_pid=pid)
        atomic(self.registry.root/'active.json',dict(release_id=self.spec['id'],revision=self.spec['revision'],root=str(root),runtime=self.paths['runtime']))
    def verify(self,journal):
        root=Path(journal['new_root']);deadline=time.monotonic()+1800
        while time.monotonic()<deadline:
            run=read(BASE/'data/control/run.json');status=read(root/'training-status.json')
            if alive_run(root) and run.get('root')==str(root.resolve()) and status.get('run_id')==run.get('run_id') and status.get('status')=='running' and status.get('phase') in ('learning','paused','evaluation'):return
            if not alive_run(root) and time.monotonic()>deadline-1750:raise RuntimeError('new runner exited')
            time.sleep(5)
        raise TimeoutError('operational health not confirmed')
    def rollback(self,journal,notify):
        old=journal.get('old_run')
        if not old:return
        new=journal.get('new_root')
        active=read(self.registry.root/'active.json')
        if active and new and active.get('root') not in (new,old['root']):raise ValueError('a newer release is active')
        if new and alive_run(new):stop_run(new,'release rollback:'+self.spec['id']+'\n',notify)
        root=Path(old['root']);flag=root/'STOP'
        if flag.exists():
            if flag.read_text()!=journal.get('stop_marker'):
                if not new:return
                raise ValueError('old run has a different stop owner')
            flag.unlink()
        if not alive_run(root):
            if not old.get('source'):raise ValueError('old source unavailable')
            pid=spawn(root,old['source'],old['kind'],old['pilot'],Path(old['cwd']),None,self.registry.root,self.spec['id']);notify(restored_pid=pid)
        if journal.get('old_active'):atomic(self.registry.root/'active.json',journal['old_active'])
        else:(self.registry.root/'active.json').unlink(missing_ok=True)
        # Verify the restored coordinator registered its real operational root.
        deadline=time.monotonic()+1800
        while time.monotonic()<deadline:
            run=read(BASE/'data/control/run.json');status=read(root/'training-status.json')
            if alive_run(root) and run.get('root')==str(root.resolve()) and status.get('run_id')==run.get('run_id') and status.get('status')=='running' and status.get('phase') in ('learning','paused','evaluation'):return
            time.sleep(5)
        raise TimeoutError('rollback health not confirmed')


class PagesSite:
    def __init__(self,definition,registry):self.definition=definition;self.paths=definition['paths'];self.spec=definition['spec'];self.registry=registry
    def api(self,path,method='GET'):
        import urllib.request
        account=read(BASE/'cloud/deployment.json')['cloudflare_account_id'];token=os.environ.get('CLOUDFLARE_API_TOKEN')
        if not token:raise ValueError('Cloudflare credential missing')
        url='https://api.cloudflare.com/client/v4/accounts/'+account+'/pages/projects/mw-nv'+path
        req=urllib.request.Request(url,method=method,headers={'Authorization':'Bearer '+token,'User-Agent':'Mozilla/5.0'},data=b'{}' if method=='POST' else None)
        data=json.load(urllib.request.urlopen(req,timeout=30))
        if not data.get('success'):raise ValueError('Cloudflare operation failed')
        return data['result']
    def validate(self):
        artifact=Path(self.paths['artifact']).resolve();manifest=read(artifact/'files.json')
        if not manifest or digest_files(manifest)!=self.spec['artifact'].get('sha256'):raise ValueError('Pages artifact manifest changed')
        for name,sha in manifest.items():
            path=(artifact/name).resolve()
            if not path.is_relative_to(artifact) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise ValueError('Pages artifact changed')
        if not (artifact/'viewer/dist/release-marker.json').exists():raise ValueError('release marker required')
    def prepare(self,journal,notify):
        if not journal.get('old_deployment'):
            project=self.api('');old=project.get('canonical_deployment',{}).get('id')
            if not old:raise ValueError('previous production deployment unknown')
            notify(old_deployment=old)
    def switch(self,journal,notify):
        if journal.get('new_deployment'):return
        # Recover a deploy whose HTTP result was lost, rather than deploying twice.
        marker='release:'+self.spec['id']+':'+str(self.spec['revision'])
        for d in self.api('/deployments?env=production&per_page=20'):
            if d.get('deployment_trigger',{}).get('metadata',{}).get('commit_message')==marker and d.get('latest_stage',{}).get('status')=='success':notify(new_deployment=d['id']);return
        cwd=Path(self.paths['artifact'])/'viewer';cli=BASE/'viewer/node_modules/.bin/wrangler'
        r=subprocess.run([str(cli),'pages','deploy','dist','--project-name','mw-nv','--branch','dev/v1.0.0','--commit-message',marker],cwd=cwd,env=dict(os.environ,WRANGLER_LOG_PATH='/tmp/mw-release-wrangler'),capture_output=True,text=True)
        if r.returncode:raise RuntimeError('Pages deployment failed')
        project=self.api('');new=project.get('canonical_deployment',{}).get('id')
        if not new or new==journal['old_deployment']:raise ValueError('new production deployment not confirmed')
        notify(new_deployment=new)
    def verify(self,journal):
        import urllib.request
        expected=(Path(self.paths['artifact'])/'viewer/dist/release-marker.json').read_bytes()
        for _ in range(30):
            try:
                body=urllib.request.urlopen(urllib.request.Request('https://mw-nv.pages.dev/release-marker.json',headers={'Cache-Control':'no-cache','User-Agent':'Mozilla/5.0'}),timeout=15).read()
                if body==expected and self.api('').get('canonical_deployment',{}).get('id')==journal['new_deployment']:return
            except OSError:pass
            time.sleep(2)
        raise ValueError('Pages marker mismatch')
    def rollback(self,journal,notify):
        if not journal.get('old_deployment'):return
        active=self.api('').get('canonical_deployment',{}).get('id')
        if active==journal['old_deployment']:return
        if active!=journal.get('new_deployment'):
            current=self.api('/deployments/'+active)
            marker='release:'+self.spec['id']+':'+str(self.spec['revision'])
            if current.get('deployment_trigger',{}).get('metadata',{}).get('commit_message')!=marker:raise ValueError('newer Pages deployment is active')
        self.api('/deployments/'+journal['old_deployment']+'/rollback','POST')
        if self.api('').get('canonical_deployment',{}).get('id')!=journal['old_deployment']:raise ValueError('Pages rollback not confirmed')


def digest_files(manifest):return hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
