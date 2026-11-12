"""Command-matched distillation and explicit post-pilot successor preparation."""
import argparse,hashlib,json,shutil
from pathlib import Path
import numpy as np
import torch
from .mission_initialize import initialize,identity
from .mission_env import MissionEnv
from .exploration_env import ExplorationEnv
from .mission_numpy import NumpyPolicy
from .mission_policy import export
from .decision_inputs import encode
from .self_play import atomic_json
from agents.tactics import compatible


def distill(source,target,seed=0,rounds=64,epochs=10):
    old=NumpyPolicy(source)
    if old.contract!='tactics-4':raise ValueError('requires frozen tactics-4 source')
    model=initialize(seed,exploration=True);env=MissionEnv();env.reset(seed%8000)
    view=ExplorationEnv(scenario_factory=lambda *a,**k:env.engine.world);view.reset(seed%8000)
    data=[]
    for _ in range(rounds):
        view.engine=env.engine;view._round()
        for team in ('A','B'):
            before=[];after=[]
            for prefix in range(4):
                a=compatible(env.items[team],before);b=compatible(view.items[team],after);lookup={identity(c):c for c in b};pairs=[(c['id'],lookup[identity(c)]['id']) for c in a if identity(c) in lookup]+[(64,64)]
                oldx=encode(env.raw(team),a,before,mission=True);logits=old.logits(oldx);ids,newids=map(list,zip(*pairs));target_prob=torch.softmax(torch.tensor(logits[ids]),0)
                newx=encode(view.raw(team),b,after,mission=True,contract='tactics-5');data.append((torch.tensor(newx[None]),torch.tensor(newids),target_prob))
                chosen=old.predict(oldx,np.array([i in [c['id'] for c in a]+[64] for i in range(65)]))
                if chosen==64:break
                c=next(c for c in a if c['id']==chosen)
                if identity(c) not in lookup:break
                before.append(c);after.append(lookup[identity(c)])
        tick=env.engine.world.tick
        while env.agents and env.engine.world.tick==tick:env.step({a:env.heuristic(a) for a in env.agents})
        if not env.agents:env.reset((seed+1)%8000);view.reset(seed)
    actor=[p for name,p in model.policy.mlp_extractor.named_parameters() if name.startswith('pi_')];optimizer=torch.optim.Adam(actor,lr=3e-4);losses=[]
    for _ in range(epochs):
        total=0.
        for x,ids,prob in data:
            logits=model.policy.mlp_extractor.forward_actor(x)[0,ids];loss=torch.nn.functional.kl_div(torch.log_softmax(logits,0),prob,reduction='sum');optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(actor,.5);optimizer.step();total+=float(loss.detach())
        losses.append(total/max(1,len(data)))
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True);model.save(target);export(model,target.with_suffix('.npz'))
    report=dict(source_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),contract='tactics-5',source_contract='tactics-4',samples=len(data),matched_commands_only=True,training_seeds_only=True,kl_by_epoch=losses,critic_fresh=True,optimizer_fresh=not bool(model.policy.optimizer.state))
    atomic_json(target.with_suffix('.json'),report);return report


def prepare(pilot,root):
    from .mission_rollout import code_fingerprint
    pilot=Path(pilot).resolve();root=Path(root).resolve();state=json.loads((pilot/'state.json').read_text());gate=json.loads((pilot/'validation-gates.json').read_text())
    if state.get('contract')!='tactics-4' or state['completed_games']<192 or not state.get('pilot_report') or state['pilot_report'].get('pause',True):raise ValueError('completed nonregressing tactics-4 pilot required')
    if gate.get('code_sha256')!=code_fingerprint():raise ValueError('pilot code certificate changed')
    if (root/'current.json').exists():raise ValueError('successor already exists; resume it rather than replacing actors')
    checkpoint=pilot/json.loads((pilot/'current.json').read_text())['path']
    # A verified full recovery must identify this exact consumed generation.
    verified=[json.loads(p.read_text()) for p in (pilot/'archive-verified').glob('*.json')]
    if not any(v.get('full') and v.get('status')=='verified' and v['generation']==state['generation'] and all(v.get('policies',{}).get(f'ppo{i}.npz')==hashlib.sha256((checkpoint/f'ppo{i}.npz').read_bytes()).hexdigest() for i in (1,2)) for v in verified):raise ValueError('freeze and remotely verify exact source recovery first')
    root.mkdir(parents=True,exist_ok=True)
    for i in (1,2):distill(checkpoint/f'ppo{i}.npz',root/'initialized'/f'ppo{i}.zip',seed=8100+i)
    retention=retention_gate(checkpoint,root)
    atomic_json(root/'strategy-gates.json',dict(approved_for_exploration=retention['retained'],source_run=state['run'],source_generation=state['generation'],contract='tactics-5',code_sha256=code_fingerprint(),retention_evaluated=True,initialized_sha256={f'ppo{i}.zip':hashlib.sha256((root/'initialized'/f'ppo{i}.zip').read_bytes()).hexdigest() for i in (1,2)}))
    shutil.copy2(pilot/'validation-gates.json',root/'validation-gates.json')
    return root/'initialized'

def retention_gate(source,root,seeds=range(30000,30005)):
    from .mission_evaluate import play
    from .league_evaluate import paired_interval
    root=Path(root);path=root/'exploration-retention.json'
    report=json.loads(path.read_text()) if path.exists() else dict(results=[],complete=False)
    fingerprints={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for folder in (Path(source),root/'initialized') for p in folder.glob('ppo*.npz')}
    if report.get('fingerprints',fingerprints)!=fingerprints:raise ValueError('retention models changed')
    report['fingerprints']=fingerprints
    done={r['case'] for r in report['results']}
    for learner in (1,2):
        policies={'old':NumpyPolicy(Path(source)/f'ppo{learner}.npz'),'new':NumpyPolicy(root/'initialized'/f'ppo{learner}.npz')}
        for seed in seeds:
            for team in (0,1):
                for swap in (False,True):
                    for version,policy in policies.items():
                        case=f'{learner}:{seed}:{team}:{int(swap)}:{version}'
                        if case in done:continue
                        _,result=play(seed,'2',{team:policy},swap)
                        result.update(case=case,learner=learner,team=team,version=version,score=.5 if result['winner'] is None else float(result['winner']==team))
                        report['results'].append(result);atomic_json(path,report)
    lookup={(r['learner'],r['seed'],r['team'],r['swapped'],r['version']):r['score'] for r in report['results']}
    intervals={str(i):paired_interval([np.mean([lookup[(i,seed,t,s,'new')]-lookup[(i,seed,t,s,'old')] for t in (0,1) for s in (False,True)]) for seed in seeds]) for i in (1,2)}
    report.update(complete=True,intervals=intervals,retained=all(v['low']>=-.10 for v in intervals.values()),scope='map2_command_migration_only')
    atomic_json(path,report);return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',required=True);p.add_argument('--root',required=True);a=p.parse_args();prepare(a.pilot,a.root)
