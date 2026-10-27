"""Controlled teacher ablation; frozen evaluations never call NIM or update policies."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
from .self_play import atomic_json


def run(root,source,updates=24):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True);source=Path(source).resolve()
    report=dict(source=str(source.name),updates=updates,strategic_improvement_established=False,trials={})
    for lane in ('baseline','enhanced'):
        target=root/lane;target.mkdir(exist_ok=True)
        # Local status/control/ledger stay isolated, while every trial shares the real request lease.
        broker=Path(__file__).resolve().parents[1]/'data/nim-budget';broker.mkdir(parents=True,exist_ok=True)
        (target/'data').mkdir(exist_ok=True);link=target/'data/nim-budget'
        if not link.exists():link.symlink_to(broker,target_is_directory=True)
        if link.resolve()!=broker:raise ValueError('comparison must share the global NIM budget')
        start=time.monotonic()
        environment=dict(os.environ,MW_NV_MISSION_TEACHER_BASELINE='1' if lane=='baseline' else '0',MW_NV_PUBLISH_TRAINING='0',MW_NV_EXPERIMENT_SEED='8021',MW_NV_CONTROL_ROOT=str(target/'control'),MW_NV_ACTIVITY_ROOT=str(target/'activity'),PYTHONPATH=str(Path(__file__).resolve().parents[1]))
        before=json.loads((target/'state.json').read_text()).get('generation',0) if (target/'state.json').exists() else 0
        if before>updates:raise ValueError('comparison trial exceeds fixed update budget')
        if before<updates:subprocess.run([sys.executable,'-m','learning.accelerated_league','--kind','mission','--root',str(target),'--source',str(source),'--updates',str(updates-before),'--workers','1'],env=environment,cwd=target,check=True)
        training_seconds=time.monotonic()-start
        # Both trials begin from the same two source models and use fixed schedules/RNG.
        from .mission_state import load
        from .mission_env import MissionEnv,MissionTeacher
        import torch
        env=MissionEnv();env.reset(0)
        buffers=[MissionTeacher(),MissionTeacher()];models,state=load(target,env,buffers,MissionTeacher(),[torch.Generator(),torch.Generator()])
        if state['generation']!=updates:raise ValueError('comparison training interrupted before target budget')
        from .mission_evaluate import evaluate
        result=evaluate(target,models,state,seeds=range(10000,10005),stage='teacher-ablation')
        report['trials'][lane]=dict(generation=state['generation'],games=state['completed_games'],elapsed_seconds=time.monotonic()-start,last_training_invocation_seconds=training_seconds,last_invocation_updates=updates-before,teacher_stats=state.get('teacher_stats',{}),teacher_samples=[len(b.rows) for b in buffers],evaluation=result)
        atomic_json(root/'comparison.json',report)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--source',required=True);p.add_argument('--updates',type=int,default=24);a=p.parse_args();run(a.root,a.source,a.updates)
