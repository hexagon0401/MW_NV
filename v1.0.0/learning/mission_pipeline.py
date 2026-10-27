"""Resume versioned mission migration without modifying an active legacy learner."""
import argparse,fcntl,hashlib,json
from pathlib import Path
from .mission_initialize import distill
from .mission_rollout import run,code_fingerprint
from .self_play import atomic_json


def prepare(root,legacy):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    with (root/'prepare.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        certificate=json.loads((root/'validation.json').read_text())
        if certificate.get('code_sha256')!=code_fingerprint() or not certificate.get('static_checks_passed') or not certificate.get('geometry_complete'):raise ValueError('current static/geometry certificate required')
        archive=json.loads((root/'source-archive.json').read_text())
        if not archive or not all(r.get('status')=='verified' for r in archive):raise ValueError('verified source policies required')
        for learner in (1,2):
            source=root/'migration-sources'/f'ppo{learner}.npz';target=root/'migrated'/f'ppo{learner}.zip';proof=target.with_suffix('.json')
            previous=json.loads(proof.read_text()) if proof.exists() else {}
            if target.exists() and target.with_suffix('.npz').exists() and previous.get('contract')=='tactics-4' and previous.get('source_sha256')==hashlib.sha256(source.read_bytes()).hexdigest():continue
            atomic_json(root/'preparation.json',dict(stage='distillation',learner=f'PPO{learner}',critic_fresh=True,optimizer_fresh=True))
            distill(source,target,40+learner,64,20)
        atomic_json(root/'preparation.json',dict(stage='validation',models_ready=True))
        return run(root,legacy)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='data/mission-normalization-v2');p.add_argument('--legacy',default='data/league-v1');a=p.parse_args();prepare(a.root,a.legacy)
