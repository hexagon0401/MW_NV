import argparse
import json,shutil,hashlib
from pathlib import Path
from server.releases import Registry
from server.release_artifacts import sandbox,verify,fingerprint
from server.telemetry import atomic
from learning.candidate_policy import CandidatePolicy
from sb3_contrib import MaskablePPO
import numpy as np
args=argparse.ArgumentParser();args.add_argument('--revision',type=int,required=True);options=args.parse_args();revision=options.revision
base=Path.cwd();legacy=base/'data/league-v1';old=base/'data/preserved/before-t24-checkpoint-00000476-f0fa0903'
registry=Registry(base/'data/releases');root=registry.root/f'comparisons/policy-progress-r{revision}';root.mkdir(parents=True,exist_ok=False);(root/'baseline').mkdir(exist_ok=True)
runtime=Path(json.loads((registry.root/'legacy-runtime.json').read_text())['runtime']);sha=fingerprint(runtime);verify(runtime,sha);sandbox(runtime,root/'sandbox',base)
for attempt in range(3):
 try:
  current=legacy/json.loads((legacy/'current.json').read_text())['path'];state=json.loads((current/'state.json').read_text())
  for i in (1,2):
   shutil.copy2(current/f'ppo{i}.zip',root/f'ppo{i}.zip');shutil.copy2(current/f'ppo{i}.npz',root/f'ppo{i}.npz');shutil.copy2(old/f'ppo{i}.npz',root/'baseline'/f'ppo{i}.npz')
  break
 except FileNotFoundError:
  if attempt==2:raise
for i in (1,2):
 policy=CandidatePolicy(root/f'ppo{i}.npz');CandidatePolicy(root/'baseline'/f'ppo{i}.npz');model=MaskablePPO.load(root/f'ppo{i}.zip',device='cpu');mask=np.ones(65,dtype=bool);obs=np.zeros(1056,dtype=np.float32);assert int(model.predict(obs,deterministic=True,action_masks=mask)[0])==policy.predict(obs,mask)
shutil.copy2(base/'server/policy_comparison.py',root/'runner.py')
atomic(root/'manifest.json',dict(base=str(base),old_games=200,new_games=state['completed_games'],generation=state['generation'],rules_version='combined-arms-4',contract='tactics-2',release_id='policy-progress-comparison',models_frozen=True,learning=False,nim=False,seeds=list(range(10000,10005))))
files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'runner.py',root/'manifest.json',*[root/f'ppo{i}.{ext}' for i in (1,2) for ext in ('zip','npz')],*[root/'baseline'/f'ppo{i}.npz' for i in (1,2)]]}
spec=dict(id='policy-progress-comparison',revision=revision,title='과거 200경기 정책 vs 최신 고정 정책 비교',description=f"200경기 시점과 {state['completed_games']}경기 시점 정책을 맵2에서 평가합니다. 양 진영·시작 위치 교대, 보류 seed5개, 과거 정책/알고리즘 상대 총80경기. NIM·학습·정책 자동 교체 없음. 직접 시작하면 CPU여유를 기다립니다.",targets=['evaluation'],dependencies=[],handler='policy_comparison',artifact=dict(artifact_id=f'policy-progress-r{revision}',files=files,runtime_digest=sha),validation_plan=['artifacts'],planned=False)
atomic(registry.root/'definitions/policy-progress-comparison.json',dict(spec=spec,paths=dict(root=str(root),runtime=str(runtime))));registry.register(spec)
from server.release_service import refresh
refresh(registry);print('comparison',registry.get(spec['id'])['status'],'snapshot games',state['completed_games'])
