"""Resumable validation pipeline; the legacy worker is untouched until every gate passes."""
import argparse,fcntl,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from .self_play import atomic_json
from .mission_evaluate import audit,migration_gate


def code_fingerprint():
    files=sorted(p for folder in ('engine','agents','learning','config','server') for p in Path(folder).glob('*') if p.suffix in ('.py','.yaml'))
    return hashlib.sha256(b''.join(str(p).encode()+p.read_bytes() for p in files)).hexdigest()


def run(root,legacy):
    root=Path(root);legacy=Path(legacy);root.mkdir(parents=True,exist_ok=True);identity=code_fingerprint();status=dict(stage='validation',status='running',code_sha256=identity,started_at=time.time(),mixed_training_started=False)
    def report(stage,**extra):
        if identity!=code_fingerprint():raise ValueError('code changed during validation; keep legacy worker and restart this pipeline')
        status.update(stage=stage,updated_at=time.time(),**extra);atomic_json(root/'rollout-status.json',status)
    def progress(*_):
        if (root/'VALIDATION_STOP').exists():raise InterruptedError('validation paused; legacy training remains active')
        if time.time()-status.get('updated_at',0)>30:report(status['stage'])
    try:
        certificate=root/'validation.json'
        validation=json.loads((certificate if certificate.exists() else Path('docs/multi-mode/validation.json')).read_text())
        if validation.get('code_sha256')!=identity:raise ValueError('static validation belongs to different code')
        if not validation['static_checks_passed'] or not validation['geometry_complete']:raise ValueError('static/geometry validation incomplete')
        proof=root/'source-archive.json'
        if not proof.exists():proof=Path('docs/multi-mode/source-archive.json')
        if not proof.exists() or not all(p['status']=='verified' for p in json.loads(proof.read_text())):raise ValueError('source actor archive not verified')
        pin=root/'validation-code.json'
        if pin.exists() and json.loads(pin.read_text())['sha256']!=identity:
            if any((root/name).exists() for name in ('engine-audit.json','migration-retention.json')):raise ValueError('validation report belongs to different code; preserve reports and start a new validation directory')
        atomic_json(pin,dict(sha256=identity));report('engine_audit');engine=audit(root,progress=progress)
        if not engine['complete'] or len(engine['results'])!=30 or not all(row.get('complete') and row.get('replay_hash_verified') for row in engine['results']):raise ValueError('engine diagnostic incomplete')
        report('migration_retention');retention=migration_gate(root,progress=progress)
        if not retention['retained'] and not any(v['high']<-.10 for v in retention['intervals'].values()):
            report('migration_retention_confirmation');retention=migration_gate(root,seeds=(*range(10000,10005),*range(10040,10060)),progress=progress)
        if not retention['retained']:
            atomic_json(root/'validation-gates.json',dict(approved_for_pilot=False,reason='map2_retention_not_established',retention=retention['intervals']));report('paused',status='paused',reason='map2_retention_not_established');return status
        # Validation authorizes an isolated pilot, never an operational switch.
        atomic_json(root/'validation-gates.json',dict(approved_for_pilot=True,code_sha256=identity,engine_games=30,retention=retention['intervals'],source_archive_verified=True,production_apply_required=True))
        report('candidate_validated',status='validated',mixed_training_started=False)

    except (OSError,ValueError,KeyError,RuntimeError,InterruptedError) as exc:
        status.update(stage='paused',status='paused',reason=str(exc)[:400],updated_at=time.time());atomic_json(root/'rollout-status.json',status)

    return status

if __name__=='__main__':
    import torch
    torch.set_num_threads(1);p=argparse.ArgumentParser();p.add_argument('--root',default='data/multi-mode-v1');p.add_argument('--legacy',default='data/league-v1');a=p.parse_args();root=Path(a.root);root.mkdir(parents=True,exist_ok=True)
    lock=(root/'rollout.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('validation pipeline already running')
    (root/'rollout.pid').write_text(str(os.getpid()));print(json.dumps(run(root,a.legacy)),flush=True)
