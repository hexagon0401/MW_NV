"""Frozen cross-side comparisons and resumable full-length engine diagnostics."""
import hashlib,json,math
from pathlib import Path
from collections import defaultdict,Counter
import numpy as np
from engine.runtime import Engine
from engine.multi_scenario import create
from engine.orders import OrderError
from engine.viewer_export import frame
from .mission_numpy import NumpyPolicy
from .mission_policy import export
from .mission_features import vector
from .candidate_policy import CandidatePolicy as LegacyPolicy,vector as legacy_vector
from .mission_statistics import collect
from .league_evaluate import paired_interval
from server.telemetry import Activity
from .self_play import atomic_json
from agents.mission_tactics import candidates,commands
from agents.tactics import candidates as legacy_candidates,compatible


def play(seed,scenario_id,policies=None,swap=False,progress=None,limit=None,record=False,scenario_factory=None,activity_role='diagnostic',activity_run='T11'):
    from engine.replay import RecordingEngine
    world=scenario_factory(seed,swap=swap) if scenario_factory else create(seed,swap=swap,scenario_id=scenario_id)
    e=(RecordingEngine if record else Engine)(world);w=e.world;initial=frame(w);history={0:[],1:[]};policies=policies or {};decisions=0
    with Activity(activity_role,f'{scenario_id}:{seed}:{int(swap)}',activity_run,str(scenario_id),[getattr(p,'policy_id','algorithm') for p in policies.values()]) as activity:
        while not getattr(w,'ended',False) and (limit is None or w.tick*.2<limit):
            # Both observations fixed before either team submits; no enemy command leakage.
            observations={t:e.observe(t) for t in (0,1)};batches={}
            for t in (0,1):
                o=observations[t];o['recent_summary']=[];policy=policies.get(t);old=isinstance(policy,LegacyPolicy);items=(legacy_candidates if old else candidates)(o);selected=[]
                for _ in range(4):
                    available=compatible(items,selected);mask=np.zeros(65,dtype=bool);mask[64]=True
                    for c in available:mask[c['id']]=True
                    from .decision_inputs import encode
                    x=encode(o,available,selected,mission=not old)
                    action=policy.predict(x,mask) if policy else max(available,key=lambda c:(c['score'],-c['id']))['id'] if available else 64
                    if action==64:break
                    selected.append(next(c for c in available if c['id']==action))
                batches[t]=commands(o,selected)
            for t in (0,1):
                for command in batches[t]:
                    try:e.submit_for(t,command)
                    except OrderError:pass
            before=w.tick;e.step(10);decisions+=1
            activity.update(w.tick)
            if progress:
                if hasattr(progress,'advance_simulation'):progress.advance_simulation((w.tick-before)*.2)
                progress('evaluation')
    return e,dict(seed=seed,scenario_id=str(scenario_id),swapped=swap,complete=bool(getattr(w,'ended',False)),winner=None if getattr(w,'winner',None) is None else int(w.winner),scores=[w.teams[t].score for t in (0,1)],tick=w.tick,hash=w.checksum(),metrics=collect(w,initial),failures=dict(Counter(ev['payload'].get('reason','unknown') for ev in w.events if ev['event_kind']=='ORDER_FAILED')))


def evaluate(root,models,state,progress=None,seeds=range(10000,10005),stage='standard'):
    root=Path(root);directory=root/'evaluations'/(f'games-{state["completed_games"]:08d}'+('' if stage=='standard' else '-'+stage));directory.mkdir(parents=True,exist_ok=True);path=directory/'report.json'
    for i,m in enumerate(models):
        if not (directory/f'ppo{i+1}.npz').exists():export(m,directory/f'ppo{i+1}.npz')
    report=json.loads(path.read_text()) if path.exists() else dict(complete=False,results=[],stage=stage)
    completed={r['case'] for r in report['results']}
    for mode in ('2','3','4'):
        for learner in (1,2):
            policy=NumpyPolicy(directory/f'ppo{learner}.npz');initial=NumpyPolicy(root/'baseline'/f'ppo{learner}.npz')
            for opponent in ('initial','algorithm'):
                for seed in seeds:
                    for team in (0,1):
                        for swap in (False,True):
                            case=f'{mode}:{learner}:{opponent}:{seed}:{team}:{int(swap)}'
                            if case in completed:continue
                            e,result=play(seed,mode,{team:policy,1-team:initial if opponent=='initial' else None},swap,progress,activity_role='evaluation',activity_run=state['run'])
                            from .results import record_world
                            match_id=state['run']+'-eval-'+str(state['completed_games'])+'-'+hashlib.sha256(case.encode()).hexdigest()[:16]
                            record_world('data/results.sqlite',e.world,'evaluation',{('A','B')[team]:policy.policy_id,('A','B')[1-team]:initial.policy_id if opponent=='initial' else 'algorithm'},match_id=match_id,metadata={'league':dict(run=state['run'],assignments={('A','B')[team]:f'PPO{learner}',('A','B')[1-team]:opponent},evaluation_games=state['completed_games'],frozen_policy=policy.policy_id)})
                            result.update(case=case,learner=f'PPO{learner}',opponent=opponent,team=team,score=.5 if result['winner'] is None else float(result['winner']==team));report['results'].append(result);atomic_json(path,report)
    report['complete']=True;atomic_json(path,report);return report


def initial_complete(root):
    try:return json.loads((Path(root)/'evaluations/games-00000000/report.json').read_text())['complete']
    except (OSError,ValueError,KeyError):return False


def pilot_report(root,state,stage='standard'):
    root=Path(root);suffix='' if stage=='standard' else '-'+stage
    paths=[root/'evaluations'/('games-'+f'{n:08d}'+suffix)/'report.json' for n in (0,state['completed_games'])]
    if any(not p.exists() for p in paths):return dict(pause=True,evidence='insufficient',reason='missing evaluation')
    before,after=[json.loads(p.read_text()) for p in paths]
    if not before['complete'] or not after['complete']:return dict(pause=True,evidence='insufficient',reason='incomplete evaluation')
    baseline={r['case']:r for r in before['results']};groups=defaultdict(lambda:defaultdict(list))
    for row in after['results']:
        if row['case'] in baseline:groups[row['scenario_id']+':'+row['learner']][row['seed']].append(row['score']-baseline[row['case']]['score'])
    modes={k:paired_interval([np.mean(v) for v in seeds.values()]) for k,seeds in groups.items()}
    result=dict(pause=any(v['high']<-.10 for v in modes.values()),modes=modes,evidence='observed_change_only',strategic_improvement_proven=False,new_map_transfer=False)
    atomic_json(root/('pilot-report.json' if stage=='standard' else 'confirmation-report.json'),result);return result


def confirm(root,models,state,progress=None):
    from sb3_contrib import MaskablePPO
    baseline=[MaskablePPO.load(Path(root)/'baseline'/f'ppo{i}.zip') for i in (1,2)]
    evaluate(root,baseline,dict(state,completed_games=0),progress,seeds=range(10020,10040),stage='confirmation')
    evaluate(root,models,state,progress,seeds=range(10020,10040),stage='confirmation')
    return pilot_report(root,state,stage='confirmation')


def migration_gate(root,seeds=range(10000,10005),progress=None):
    root=Path(root);path=root/'migration-retention.json';report=json.loads(path.read_text()) if path.exists() else dict(complete=False,results=[]);done={r['case'] for r in report['results']}
    fingerprints={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('migration-sources','migrated') for p in sorted((root/folder).glob('ppo*.npz'))}
    if report.get('fingerprints',fingerprints)!=fingerprints:raise ValueError('migration evaluation model changed; use a new report directory')
    report['fingerprints']=fingerprints
    for learner in (1,2):
        policies={'old':LegacyPolicy(root/'migration-sources'/f'ppo{learner}.npz'),'new':NumpyPolicy(root/'migrated'/f'ppo{learner}.npz')}
        for seed in seeds:
            for team in (0,1):
                for swap in (False,True):
                    for version,policy in policies.items():
                        case=f'{learner}:{seed}:{team}:{int(swap)}:{version}'
                        if case in done:continue
                        _,result=play(seed,'2',{team:policy},swap,progress,activity_role='evaluation');result.update(case=case,learner=learner,team=team,version=version,score=.5 if result['winner'] is None else float(result['winner']==team));report['results'].append(result);atomic_json(path,report)
    lookup={(r['learner'],r['seed'],r['team'],r['swapped'],r['version']):r['score'] for r in report['results']};intervals={}
    for learner in (1,2):
        differences=[np.mean([lookup[(learner,seed,t,s,'new')]-lookup[(learner,seed,t,s,'old')] for t in (0,1) for s in (False,True)]) for seed in seeds];intervals[str(learner)]=paired_interval(differences)
    report.update(complete=True,intervals=intervals,retained=all(v['low']>=-.10 for v in intervals.values()),evidence='frozen_map2_only');atomic_json(path,report);return report


def audit(root,count=10,progress=None):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);path=root/'engine-audit.json';report=json.loads(path.read_text()) if path.exists() else dict(complete=False,results=[]);done={(r['scenario_id'],r['seed']) for r in report['results']}
    for mode in ('2','3','4'):
        for seed in range(count):
            if (mode,seed) in done:continue
            e,result=play(seed,mode,swap=bool(seed%2),progress=progress,record=True)
            from engine.replay import replay
            result['replay_hash_verified']=replay(e.document()).checksum()==result['hash']
            report['results'].append(result);atomic_json(path,report)
    report['complete']=True;report['counts']=dict(Counter(r['scenario_id'] for r in report['results']));atomic_json(path,report);return report

def ensure_initial_worker(root,state):
    import os,sys,subprocess
    root=Path(root).resolve()
    if initial_complete(root):return False
    pidfile=root/'initial-evaluation.pid'
    try:
        pid=int(pidfile.read_text());args=(Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0')
        if b'learning.mission_evaluate' in args and str(root).encode() in args:return True
    except (OSError,ValueError):pass
    atomic_json(root/'initial-evaluation-state.json',dict(run=state['run'],generation=0,completed_games=0))
    log=(root/'initial-evaluation.log').open('ab');environment=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MW_NV_TORCH_THREADS='1')
    process=subprocess.Popen([sys.executable,'-u','-m','learning.mission_evaluate','initial','--root',str(root)],stdout=log,stderr=log,stdin=subprocess.DEVNULL,start_new_session=True,env=environment);log.close();pidfile.write_text(str(process.pid));return True


if __name__=='__main__':
    import argparse,torch,fcntl,shutil
    torch.set_num_threads(1);p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','migration','initial']);p.add_argument('--root',default='data/multi-mode-v1');a=p.parse_args();root=Path(a.root)
    lock=(root/(a.action+'.lock')).open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('evaluation already running')
    if a.action=='initial':
        state=json.loads((root/'initial-evaluation-state.json').read_text());directory=root/'evaluations/games-00000000';directory.mkdir(parents=True,exist_ok=True)
        for i in (1,2):
            if not (directory/f'ppo{i}.npz').exists():shutil.copy2(root/'baseline'/f'ppo{i}.npz',directory/f'ppo{i}.npz')
        def progress(*_):
            if (root/'STOP').exists():raise InterruptedError('evaluation stopped')
        try:evaluate(root,[None,None],state,progress)
        except InterruptedError:pass
    else:(audit if a.action=='audit' else migration_gate)(root)
