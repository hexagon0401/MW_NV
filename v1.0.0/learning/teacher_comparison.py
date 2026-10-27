"""Controlled teacher ablation; frozen evaluations never call NIM or update policies."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
from .self_play import atomic_json


def run(root,source,updates=24):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True);source=Path(source).resolve()
    report=dict(source=str(source.name),updates=updates,strategic_improvement_established=False,trials={})
    for lane in ('baseline','enhanced'):
        target=root/lane;target.mkdir(exist_ok=True);start=time.monotonic()
        environment=dict(os.environ,MW_NV_MISSION_TEACHER_BASELINE='1' if lane=='baseline' else '0',MW_NV_PUBLISH_TRAINING='0',MW_NV_EXPERIMENT_SEED='8021',MW_NV_CONTROL_ROOT=str(target/'control'),MW_NV_ACTIVITY_ROOT=str(target/'activity'),PYTHONPATH=str(Path(__file__).resolve().parents[1]))
        subprocess.run([sys.executable,'-m','learning.accelerated_league','--kind','mission','--root',str(target),'--source',str(source),'--updates',str(updates),'--workers','1'],env=environment,cwd=target,check=True)
        # Both trials begin from the same two source models and use fixed schedules/RNG.
        from .mission_state import load
        from .mission_env import MissionEnv,MissionTeacher
        import torch
        env=MissionEnv();env.reset(0)
        models,state=load(target,env,[MissionTeacher(),MissionTeacher()],MissionTeacher(),[torch.Generator(),torch.Generator()])
        from .mission_evaluate import evaluate
        result=evaluate(target,models,state,seeds=range(10000,10005),stage='teacher-ablation')
        report['trials'][lane]=dict(generation=state['generation'],games=state['completed_games'],elapsed_seconds=time.monotonic()-start,evaluation=result)
        atomic_json(root/'comparison.json',report)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--source',required=True);p.add_argument('--updates',type=int,default=24);a=p.parse_args();run(a.root,a.source,a.updates)
