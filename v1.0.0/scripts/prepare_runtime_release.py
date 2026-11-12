"""Stage runtime management; network probes never start PPO or mark absent gates PASS."""
import json
from pathlib import Path
import yaml
from server.release_observations import read
from server.release_service import refresh
from server.releases import Registry
from server.telemetry import atomic
from server.release_handlers import exact_recovery

def main():
    base=Path.cwd();folder=base/'data/runtime';stage=read(folder/'staged-code.json');root=Path(read(base/'data/releases/active.json')['root']);deployment=read(folder/'monitor-deployment.json')
    spec=next(row for row in yaml.safe_load((base/'config/releases.yaml').read_text())['releases'] if row['id']=='runtime-continuity');spec['artifact'].update(runtime_digest=stage['runtime_digest'])
    cfg=dict(root=str(root),runtime=stage['runtime'],runtime_digest=stage['runtime_digest'],monitor_url=deployment.get('url',''),key_file=deployment.get('key_file',str(folder/'monitor.key')),release_id=spec['id'])
    atomic(folder/'pending-config.json',cfg)
    restore=read(folder/'restore-verification.json');checks=read(folder/'checks.json');code=read(folder/'code-proof.json');remote=exact_recovery(root);proof=dict(tests=bool(checks.get('tests_passed') and checks.get('runtime_digest')==stage['runtime_digest']),recovery=bool(restore.get('passed') and remote and restore.get('checkpoint_sha256')==remote['sha256'] and code.get('verified') and code.get('runtime_digest')==stage['runtime_digest']),monitor=False)
    if deployment.get('free_confirmed'):
        from server.runtime_lease import Client
        client=Client(base,cfg);state=read(root/'state.json');client.send('acquire',state['run'],dict(state='STARTING'));client.send('release',state['run'],dict(state='OFFLINE'));proof['monitor']=True
    atomic(folder/'validation.json',proof);registry=Registry(base/'data/releases');atomic(registry.root/'definitions/runtime-continuity.json',dict(spec=spec,paths=dict(runtime=stage['runtime'],run_root=str(root),proof=str(folder/'validation.json'),config=str(folder/'pending-config.json'))));registry.register(spec);refresh(registry)
    print(registry.get(spec['id'])['status'],proof)
if __name__=='__main__':main()
