"""Typed activation of verified recovery control, preserving the current checkpoint."""
import json,time
from pathlib import Path
from .telemetry import atomic
from .release_observations import read
from .release_artifacts import verify
from .release_handlers import BASE,stop_run,archive_exact

class RuntimeManagement:
    def __init__(self,definition,registry):self.definition=definition;self.registry=registry;self.paths=definition['paths'];self.spec=definition['spec']
    def validate(self):
        verify(self.paths['runtime'],self.spec['artifact']['runtime_digest'])
        proof=read(self.paths['proof'])
        if not all(proof.get(k) for k in ('tests','recovery','monitor')):raise ValueError('required runtime validation missing')
        code=read(BASE/'data/runtime/code-proof.json')
        if not code.get('verified') or code.get('runtime_digest')!=self.spec['artifact']['runtime_digest']:raise ValueError('remote executable code not verified')
        cfg=read(self.paths['config']);key=Path(cfg['key_file'])
        if not key.is_file() or len(key.read_text().strip())<32:raise ValueError('monitor key missing')
    def prepare(self,journal,notify):
        root=Path(self.paths['run_root']);marker='release:'+self.spec['id']+'\n'
        notify(old_active=read(self.registry.root/'active.json'),old_gate=read(root/'validation-gates.json'),old_config=read(BASE/'data/runtime/config.json'),marker=marker)
        stop_run(root,marker,notify);notify(recovery=archive_exact(root))
        from .runtime_lease import Client
        cfg=read(self.paths['config']);Client(BASE,cfg).send('acquire',read(root/'state.json')['run'],dict(state='STARTING'))
    def switch(self,journal,notify):
        cfg=read(self.paths['config']);root=Path(self.paths['run_root']);active=read(self.registry.root/'active.json')
        atomic(BASE/'data/runtime/config.json',cfg)
        atomic(root/'validation-gates.json',dict(read(root/'validation-gates.json'),code_sha256=self.spec['artifact']['runtime_digest']))
        atomic(self.registry.root/'active.json',dict(active,root=str(root),runtime=self.paths['runtime'],release_id=self.spec['id'],revision=self.spec['revision']))
        if (root/'STOP').exists():
            if (root/'STOP').read_text()!=journal['marker']:raise ValueError('stop marker belongs to another owner')
            (root/'STOP').unlink()
        from .runtime_recovery import publish_pointer
        publish_pointer(root,journal['recovery'],BASE)
        notify(activated=True)
    def verify(self,journal):
        from .runtime_supervisor import bootstrap
        bootstrap(BASE);deadline=time.monotonic()+600
        while time.monotonic()<deadline:
            h=read(BASE/'data/runtime/health.json')
            if h.get('lease_valid') and h.get('state') in ('RUNNING','PAUSED'):return
            time.sleep(2)
        raise TimeoutError('runtime recovery health did not become ready')
    def rollback(self,journal,notify):
        root=Path(self.paths['run_root']);folder=BASE/'data/runtime';atomic(folder/'lease.json',dict(deadline=0))
        (folder/'STOP').write_text('runtime rollback\n')
        stop_run(root,journal.get('marker','runtime rollback\n'),notify)
        atomic(self.registry.root/'active.json',journal['old_active']);atomic(root/'validation-gates.json',journal['old_gate'])
        if journal.get('old_config'):atomic(folder/'config.json',journal['old_config'])
        else:(folder/'config.json').unlink(missing_ok=True)
        if (root/'STOP').exists() and (root/'STOP').read_text()==journal.get('marker'):(root/'STOP').unlink()
        notify(restored=True)
