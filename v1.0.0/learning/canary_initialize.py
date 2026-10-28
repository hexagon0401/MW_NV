"""Prepare a verified mixed-policy source; never train or publish a match here."""
import argparse,fcntl,hashlib,json,os,random,shutil,time,uuid
from pathlib import Path
import numpy as np
import torch
from sb3_contrib import MaskablePPO
from .mission_env import MissionEnv,MissionTeacher
from .mission_state import save
from .mission_policy import export
from .league_archive import spool,publish_pending
from server.release_artifacts import sandbox,verify
from server.telemetry import atomic,process_start


def run(definition,base):
    paths=definition['paths'];root=Path(paths['pilot']);root.mkdir(parents=True,exist_ok=True)
    lock=(root/'pilot.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    atomic(root/'pilot.pid.json',dict(pid=os.getpid(),start=process_start(os.getpid())))
    verify(paths['runtime'],definition['spec']['artifact']['runtime_digest'])
    source=Path(paths['validation'])/'migrated';gate=json.loads((Path(paths['validation'])/'validation-gates.json').read_text())
    if gate.get('engine_games')!=30 or gate.get('release_profile')!='canary':raise ValueError('canary engine gates required')
    cwd=sandbox(paths['runtime'],root/'sandbox',base);os.chdir(cwd)
    atomic(root/'validation-gates.json',gate);random.seed(771);np.random.seed(771);torch.manual_seed(771);torch.set_num_threads(1)
    if not (root/'current.json').exists():
        for name in ('opponents','baseline','evaluations','insights'):(root/name).mkdir(exist_ok=True)
        models=[MaskablePPO.load(source/f'ppo{i}.zip',device='cpu') for i in (1,2)]
        env=MissionEnv(decision_seconds=10);env.reset(0)
        state=dict(schema=1,run='canary-'+uuid.uuid4().hex[:12],rules_version='combined-arms-6',catalog_version='combined-arms-3',contract='tactics-4',map_id='mixed-2-3-4',map_version='1',generation=0,completed_games=0,episode=0,active=False,rounds=0,last_policy_archive=0,last_full_archive=0,last_evaluation=0,assignments={},teacher_enabled=True,canary=True,performance_verified=False,source_sha256=[hashlib.sha256((source/f'ppo{i}.npz').read_bytes()).hexdigest() for i in (1,2)])
        for i,m in enumerate(models,1):export(m,root/'baseline'/f'ppo{i}.npz');m.save(root/'baseline'/f'ppo{i}.zip')
        save(root,models,env,[MissionTeacher(),MissionTeacher()],MissionTeacher(),[torch.Generator().manual_seed(902+i) for i in range(2)],state)
    folder=root/json.loads((root/'current.json').read_text())['path'];state=json.loads((folder/'state.json').read_text())
    if not state.get('canary') or state['generation']!=0:raise ValueError('canary source changed')
    spool(root,folder,state,True);result=publish_pending(root)
    atomic(root/'pilot-status.json',dict(status='CANARY_PREPARED' if result['status']=='verified' else 'WAITING_ARCHIVE',release_profile='canary',updated_at=time.time()))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--definition',required=True);p.add_argument('--registry-root');p.add_argument('--base',required=True);a=p.parse_args();run(json.loads(Path(a.definition).read_text()),a.base)
