"""Distill two preserved specialists independently; never modifies the originals."""
import argparse,json,hashlib,random,uuid
from pathlib import Path
import numpy as np
import torch
from learning.mission_initialize import distill
from learning.mission_env import MissionEnv,MissionTeacher
from learning.mission_state import save
from learning.mission_policy import export
from learning.league_archive import spool,publish_pending
from server.telemetry import atomic

def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--out',required=True);a=p.parse_args();baseline=json.loads(Path(a.baseline).read_text());source=Path(baseline['local']);root=Path(a.out).resolve();root.mkdir(parents=True,exist_ok=True);torch.set_num_threads(1)
 for name in ('baseline','opponents','evaluations','insights'):(root/name).mkdir(exist_ok=True)
 models=[]
 for i in (1,2):
  model,report=distill(source/f'ppo{i}.npz',root/'baseline'/f'ppo{i}.zip',seed=771+i,rounds=64,epochs=20);models.append(model);print('distilled',i,report['matched'],report['kl_final'],flush=True)
 env=MissionEnv(decision_seconds=10);env.reset(0)
 state=dict(schema=1,run='rotation-'+uuid.uuid4().hex[:12],rules_version='combined-arms-6',catalog_version='combined-arms-3',contract='tactics-4',map_id='mixed-2-3-4',map_version='1',generation=0,completed_games=0,episode=0,active=False,rounds=0,last_policy_archive=0,last_full_archive=0,last_evaluation=0,assignments={},teacher_enabled=True,canary=True,performance_verified=False,capture_baseline=baseline,source_sha256=[hashlib.sha256((source/f'ppo{i}.npz').read_bytes()).hexdigest() for i in (1,2)])
 folder=save(root,models,env,[MissionTeacher(),MissionTeacher()],MissionTeacher(),[torch.Generator().manual_seed(902+i) for i in range(2)],state)
 spool(root,folder,state,True);print('candidate archive:',publish_pending(root),flush=True)
if __name__=='__main__':main()
