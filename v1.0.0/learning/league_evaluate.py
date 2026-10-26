"""Frozen, resumable crossed-side evaluations; no teacher calls or PPO updates."""
import hashlib,json
from pathlib import Path
from collections import defaultdict
import numpy as np
from engine.viewer_export import frame
from .candidate_env import CandidateEnv
from .candidate_policy import CandidatePolicy,export
from .training_maps import training_scenario
from .self_play import atomic_json
from .results import record_world


def evaluate(root,models,state,progress=None,seeds=range(10000,10005),scenario_factory=training_scenario,stage='standard'):
    root=Path(root);directory=root/'evaluations'/(f'games-{state["completed_games"]:08d}'+('' if stage=='standard' else '-'+stage));directory.mkdir(parents=True,exist_ok=True)
    for i,m in enumerate(models):
        p=directory/f'ppo{i+1}.npz'
        if not p.exists():export(m,p)
    path=directory/'report.json'
    report=json.loads(path.read_text()) if path.exists() else dict(schema=1,run=state['run'],games=state['completed_games'],generation=state['generation'],stage=stage,complete=False,results=[])
    completed={r['case']:r for r in report['results']};cache={r['cache']:r for r in report['results']}
    for i in range(2):
        policy=CandidatePolicy(directory/f'ppo{i+1}.npz');baseline=CandidatePolicy(root/'baseline'/f'ppo{i+1}.npz')
        for opponent_name in ('initial','algorithm'):
            for seed in seeds:
                for team in ('A','B'):
                    for swap in (False,True):
                        case=f'{i}:{opponent_name}:{seed}:{team}:{int(swap)}'
                        if case in completed:continue
                        identity=f'{policy.policy_id}:{baseline.policy_id if opponent_name=="initial" else "algorithm"}:{seed}:{team}:{int(swap)}'
                        if identity in cache:
                            result=dict(cache[identity],case=case,learner=f'PPO{i+1}',reused=True)
                        else:
                            env=CandidateEnv(scenario_factory=scenario_factory,decision_seconds=10);env.reset(seed,options={'swap':swap});initial=frame(env.engine.world);other='B' if team=='A' else 'A'
                            while env.agents:
                                action={a:(policy.predict(env.vector(a),env.mask(a)) if a==team else baseline.predict(env.vector(a),env.mask(a)) if opponent_name=='initial' else env.heuristic(a)) for a in env.agents};env.step(action)
                                if progress:progress('evaluation')
                            w=env.engine.world;score=.5 if w.winner is None else float(int(w.winner)==('A','B').index(team))
                            policies={team:policy.policy_id,other:baseline.policy_id if opponent_name=='initial' else 'algorithm'}
                            mid=f'{state["run"]}-eval-{state["completed_games"]}-{hashlib.sha256(identity.encode()).hexdigest()[:16]}'
                            record_world('data/results.sqlite',w,'evaluation',policies,match_id=mid,initial_frame=initial,metadata={'league':dict(run=state['run'],assignments={team:f'PPO{i+1}',other:opponent_name},evaluation_games=state['completed_games'],frozen_policy=policy.policy_id)})
                            result=dict(case=case,cache=identity,learner=f'PPO{i+1}',policy=policy.policy_id,opponent=opponent_name,seed=seed,team=team,swapped=swap,score=score,scores=[w.teams[t].score for t in (0,1)],match_id=mid,reused=False)
                        report['results'].append(result);completed[case]=result;cache[identity]=result;atomic_json(path,report)
    report['complete']=True;atomic_json(path,report);return report


def paired_interval(differences,seed=419):
    x=np.asarray(differences,dtype=float)
    if not len(x):return None
    rng=np.random.default_rng(seed);samples=x[rng.integers(0,len(x),(5000,len(x)))].mean(axis=1)
    return dict(mean=float(x.mean()),low=float(np.quantile(samples,.025)),high=float(np.quantile(samples,.975)),seeds=len(x))


def pilot_report(root,state):
    root=Path(root);baseline=json.loads((root/'evaluations'/'games-00000000'/'report.json').read_text())
    candidates=[p for p in (root/'evaluations').glob('games-*/report.json') if len(p.parent.name.split('-'))==2 and int(p.parent.name.split('-')[1])>=state['pilot']]
    if not candidates:return dict(pause=True,reason='missing pilot evaluation',evidence='insufficient')
    current=json.loads(sorted(candidates)[-1].read_text())
    if not baseline['complete'] or not current['complete']:return dict(pause=True,reason='incomplete evaluation',evidence='insufficient')
    before={r['case']:r for r in baseline['results']};summary={};pause=False
    for learner in ('PPO1','PPO2'):
        groups=defaultdict(list)
        for row in current['results']:
            if row['learner']==learner and row['case'] in before:groups[row['seed']].append(row['score']-before[row['case']]['score'])
        interval=paired_interval([sum(v)/len(v) for v in groups.values()]);summary[learner]=interval
        if interval and interval['high']<-.10:pause=True
    result=dict(schema=1,run=state['run'],games=state['completed_games'],pause=pause,learners=summary,evidence='observed_change',strategic_improvement_proven=False,dual_vs_shared_proven=False)
    atomic_json(root/'pilot-report.json',result);return result


def confirm(root,models,state,progress=None):
    """Additional seeds confirm policy performance; not a tactic-causality experiment."""
    from .league_policy import initialize
    root=Path(root);seeds=range(10020,10040)
    import random,torch
    rng=(random.getstate(),np.random.get_state(),torch.get_rng_state())
    baseline_models=[initialize(root/'baseline'/f'ppo{i+1}.npz',810+i) for i in range(2)]
    random.setstate(rng[0]);np.random.set_state(rng[1]);torch.set_rng_state(rng[2])
    initial_state=dict(state,completed_games=0)
    initial=evaluate(root,baseline_models,initial_state,progress,seeds=seeds,stage='confirmation')
    current=evaluate(root,models,state,progress,seeds=seeds,stage='confirmation')
    before={r['case']:r for r in initial['results']};summary={}
    for learner in ('PPO1','PPO2'):
        groups=defaultdict(list)
        for row in current['results']:
            if row['learner']==learner:groups[row['seed']].append(row['score']-before[row['case']]['score'])
        summary[learner]=paired_interval([sum(v)/len(v) for v in groups.values()])
    result=dict(schema=1,run=state['run'],games=state['completed_games'],learners=summary,evidence={k:'reproduced_policy_improvement_in_tested_scope' if v and v['low']>0 else 'not_confirmed' for k,v in summary.items()},tactical_causality=False,new_map_transfer=False)
    atomic_json(root/'confirmation-report.json',result);return result
