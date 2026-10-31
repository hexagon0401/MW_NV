"""Controlled teacher ablation; frozen evaluations never call NIM or update policies."""
import argparse,json,os,subprocess,sys,time,resource,hashlib
from pathlib import Path
from .self_play import atomic_json


def run(root,source,updates=128,seeds=(8021,8022,8023)):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True);source=Path(source).resolve()
    report_path=root/'comparison.json'
    report=json.loads(report_path.read_text()) if report_path.exists() else dict(source=str(source.name),updates=updates,seeds=list(seeds),strategic_improvement_established=False,trials={})
    if report.get('updates')!=updates or report.get('seeds',list(seeds))!=list(seeds):raise ValueError('comparison budget changed')
    for seed,lane in [(seed,lane) for seed in seeds for lane in ('ppo_only','ordinary','enhanced')]:
        key=f'{seed}:{lane}'
        if report['trials'].get(key,{}).get('complete'):continue
        target=root/str(seed)/lane;target.mkdir(parents=True,exist_ok=True)
        # Local status/control/ledger stay isolated, while every trial shares the real request lease.
        broker=Path(__file__).resolve().parents[1]/'data/nim-budget';broker.mkdir(parents=True,exist_ok=True)
        (target/'data').mkdir(exist_ok=True);link=target/'data/nim-budget'
        if not link.exists():link.symlink_to(broker,target_is_directory=True)
        if link.resolve()!=broker:raise ValueError('comparison must share the global NIM budget')
        proof=dict(seed=seed,condition=lane,updates=updates,sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.glob('ppo*') if p.suffix in ('.zip','.npz')})
        proof_path=target/'trial-source.json'
        if proof_path.exists() and json.loads(proof_path.read_text())!=proof:raise ValueError('trial source changed')
        atomic_json(proof_path,proof)
        start=time.monotonic();cpu_start=resource.getrusage(resource.RUSAGE_CHILDREN)
        environment=dict(os.environ,MW_NV_MISSION_TEACHER_BASELINE='0',MW_NV_DISABLE_MISSION_COACH='0' if lane=='enhanced' else '1',MW_NV_PUBLISH_TRAINING='0',MW_NV_EXPERIMENT_SEED=str(seed),MW_NV_CONTROL_ROOT=str(target/'control'),MW_NV_ACTIVITY_ROOT=str(target/'activity'),PYTHONPATH=str(Path(__file__).resolve().parents[1]))
        before=json.loads((target/'state.json').read_text()).get('generation',0) if (target/'state.json').exists() else 0
        if before>updates:raise ValueError('comparison trial exceeds fixed update budget')
        if before<updates:
            command=[sys.executable,'-m','learning.accelerated_league','--kind','mission','--root',str(target),'--source',str(source),'--updates',str(updates-before),'--workers','1']
            if lane=='ppo_only':command.append('--no-teacher')
            subprocess.run(command,env=environment,cwd=target,check=True)
        training_seconds=time.monotonic()-start
        cpu_end=resource.getrusage(resource.RUSAGE_CHILDREN);usage_path=target/'training-usage.json'
        usage=json.loads(usage_path.read_text()) if usage_path.exists() else dict(wall_seconds=0.,cpu_seconds=0.,coverage='completed_training_invocations')
        usage['wall_seconds']+=training_seconds;usage['cpu_seconds']+=cpu_end.ru_utime+cpu_end.ru_stime-cpu_start.ru_utime-cpu_start.ru_stime;atomic_json(usage_path,usage)
        # Both trials begin from the same two source models and use fixed schedules/RNG.
        from .mission_state import load
        from .mission_env import MissionEnv,MissionTeacher
        import torch
        env=MissionEnv();env.reset(0)
        buffers=[MissionTeacher(),MissionTeacher()];models,state=load(target,env,buffers,MissionTeacher(),[torch.Generator(),torch.Generator()])
        if state['generation']!=updates:raise ValueError('comparison training interrupted before target budget')
        from .mission_evaluate import evaluate
        previous=Path.cwd()
        try:
            os.chdir(target)
            result=evaluate(target,models,state,seeds=range(10000,10005),stage='teacher-ablation')
        finally:os.chdir(previous)
        report['trials'][key]=dict(complete=True,usage=usage,seed=seed,condition=lane,generation=state['generation'],games=state['completed_games'],elapsed_seconds=time.monotonic()-start,last_training_invocation_seconds=training_seconds,last_invocation_updates=updates-before,teacher_stats=state.get('teacher_stats',{}),teacher_samples=[len(b.rows) for b in buffers],evaluation=result)
        atomic_json(root/'comparison.json',report)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--source',required=True);p.add_argument('--updates',type=int,default=128);a=p.parse_args();run(a.root,a.source,a.updates)
