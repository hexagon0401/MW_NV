"""Atomic two-learner checkpoints, explicit rules checks and complete RNG state."""
import gzip,json,random,shutil,uuid,sqlite3
from pathlib import Path
import numpy as np
import torch
from sb3_contrib import MaskablePPO
from stable_baselines3.common.logger import configure
from engine.replay import encode,decode
from engine.runtime import Engine
RULES_VERSION='combined-arms-6'
CATALOG_VERSION='combined-arms-3'
from .mission_policy import export
from .mission_numpy import NumpyPolicy as CandidatePolicy
from .self_play import atomic_json
from .checkpoint_io import write_environment


def save(root,models,env,buffers,querier,generators,state):
    root=Path(root);folder=root/'checkpoints'/f'checkpoint-{state["generation"]:08d}-{uuid.uuid4().hex[:8]}';folder.mkdir(parents=True)
    for i,model in enumerate(models):
        model.save(folder/f'ppo{i+1}.zip');export(model,folder/f'ppo{i+1}.npz');buffers[i].save(folder/f'teacher{i+1}.npz')
        for a in ('A','B'):
            obs=env.vector(a);mask=env.mask(a)
            if int(model.predict(obs,deterministic=True,action_masks=mask)[0])!=CandidatePolicy(folder/f'ppo{i+1}.npz').predict(obs,mask):raise ValueError('NumPy parity')
    if (root/'coaching').exists():
        coaching=folder/'coaching';coaching.mkdir()
        coordinator=json.loads((root/'coaching'/'state.json').read_text());shutil.copy2(root/'coaching'/'state.json',coaching/'state.json')
        for job in coordinator['jobs']:
            if (root/'coaching'/job).exists():shutil.copytree(root/'coaching'/job,coaching/job,ignore=shutil.ignore_patterns('*.partial'))
    payload=dict(scenario_id=env.scenario_id,world=env.engine.world,presentation_events=env.engine.presentation_events,agents=env.agents,items=env.items,selected=env.selected,finished=env.finished,reserved_supply=env.reserved_supply,initial_costs=env.initial_costs,history=env.history)
    write_environment(folder/'environment.json.gz',payload)
    rng=dict(python=encode(random.getstate()),numpy=None,torch=torch.get_rng_state().tolist(),actors=[g.get_state().tolist() for g in generators])
    # numpy state ndarray is handled explicitly, never through pickle.
    n=np.random.get_state();rng['numpy']=[n[0],n[1].tolist(),*n[2:]]
    atomic_json(folder/'rng.json',rng)
    for i in range(2):atomic_json(folder/f'PPO{i+1}.json',dict(learner=f'PPO{i+1}',policy=f'ppo{i+1}.npz',generation=state['generation'],rules_version=RULES_VERSION,contract='tactics-4'))
    for team in ('A','B'):atomic_json(folder/f'{team}.json',dict(team=team,learner=state.get('assignments',{}).get(team),generation=state['generation'],rules_version=RULES_VERSION,contract='tactics-4'))
    state['teacher_stats']=dict(querier.stats);state['teacher_buffers']=[dict(b.stats) for b in buffers]
    querier.save(folder/'teacher-query.npz')
    if hasattr(env,'accelerated_snapshot'):
        write_environment(folder/'environments.json.gz',env.accelerated_snapshot)
        state['runtime_schema']='adaptive-1'
    atomic_json(folder/'state.json',state)
    if (root/'validation-gates.json').exists():shutil.copy2(root/'validation-gates.json',folder/'validation-gates.json')
    if Path('data/results.sqlite').exists():
        with sqlite3.connect('data/results.sqlite') as source,sqlite3.connect(folder/'results.sqlite') as dest:source.backup(dest)
    atomic_json(root/'current.json',dict(path=str(folder.relative_to(root))));atomic_json(root/'state.json',state)
    # Archive spooling owns any files it needs before old consumed checkpoints are pruned.
    seen=set()
    for old in sorted((root/'checkpoints').glob('checkpoint-*'),key=lambda p:p.stat().st_mtime,reverse=True):
        generation=old.name.split('-')[1]
        if generation in seen or len(seen)>=2:shutil.rmtree(old)
        else:seen.add(generation)
    return folder


def load(root,env,buffers,querier,generators):
    root=Path(root);folder=root/json.loads((root/'current.json').read_text())['path'];state=json.loads((folder/'state.json').read_text())
    if state['rules_version']!=RULES_VERSION or state['contract']!='tactics-4' or state['catalog_version']!=CATALOG_VERSION:raise ValueError('incompatible league checkpoint')
    if not (root/'coaching').exists() and (folder/'coaching').exists():
        shutil.copytree(folder/'coaching',root/'coaching')
    with gzip.open(folder/'environment.json.gz','rt') as f:d=decode(json.load(f))
    env.engine=Engine(d.pop('world'));env.engine.presentation_events=d.pop('presentation_events')
    for k,v in d.items():setattr(env,k,v)
    env.cached_observations={a:env.raw(a) for a in ('A','B')};env.cached_tick=env.engine.world.tick
    models=[]
    for i in range(2):
        model=MaskablePPO.load(folder/f'ppo{i+1}.zip',device='cpu');model.set_logger(configure(folder=None,format_strings=[]));models.append(model)
        buffers[i].load(folder/f'teacher{i+1}.npz');buffers[i].stats.update(state['teacher_buffers'][i])
    querier.load(folder/'teacher-query.npz');querier.stats.update(state['teacher_stats'])
    rng=json.loads((folder/'rng.json').read_text());random.setstate(decode(rng['python']));n=rng['numpy'];np.random.set_state((n[0],np.array(n[1],dtype=np.uint32),*n[2:]));torch.set_rng_state(torch.tensor(rng['torch'],dtype=torch.uint8))
    for g,value in zip(generators,rng['actors']):g.set_state(torch.tensor(value,dtype=torch.uint8))
    return models,state


def record_update(root,state,models):
    """Called only after the durable checkpoint pointer; safe to backfill on resume."""
    if state['generation']<=0:return
    from .results import record_training
    root=Path(root);folder=root/json.loads((root/'current.json').read_text())['path']
    for i,m in enumerate(models):
        learner=f'PPO{i+1}';steps=state.get(f'ppo{i+1}_last_update',{}).get('steps',0);policy=CandidatePolicy(folder/f'ppo{i+1}.npz').policy_id
        record_training('data/results.sqlite',policy,steps,rules_version=RULES_VERSION,opponent='mission-mixed',run_id=f'{state["run"]}-{learner}-update-{state["generation"]:08d}',training_run=state['run']+':'+learner,metadata={'league':dict(run=state['run'],learner=learner,generation=state['generation'])})
