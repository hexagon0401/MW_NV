"""External geometry adapter and explicit zero-shot/equal-budget adaptation protocol."""
from pathlib import Path
import numpy as np
from .mission_evaluate import play
from .mission_numpy import NumpyPolicy
from .mission_env import MissionEnv
from .league_policy import choose,update
from .mission_env import MissionTeacher

HELD_OUT_SEEDS=range(20000,20020)
TRAIN_SEEDS=range(6000,6100)


def validate_factory(factory):
    for seed in (6000,20000):
        w=factory(seed,swap=False)
        if w.rules_version!='combined-arms-5' or w.catalog_version!='combined-arms-3' or w.mode not in ('conquest','elimination','capture_flag'):raise ValueError('external scenario requires explicit compatible rules/observation contract')
        from engine.multi_scenario import validate
        validate(w)
    return factory


def evaluate_transfer(policy,factory,seeds=HELD_OUT_SEEDS):
    """Frozen novel geometry, no teacher or gradient steps. Reuse same seeds after equal-budget tuning."""
    validate_factory(factory);model=NumpyPolicy(policy);rows=[]
    for seed in seeds:
        if seed not in HELD_OUT_SEEDS:raise ValueError('transfer evaluation seed partition')
        for team in (0,1):
            for swap in (False,True):
                _,result=play(seed,None,{team:model},swap,scenario_factory=factory);rows.append(dict(result,team=team,phase='zero_shot_or_post_tuning',policy=model.policy_id))
    return rows


def fine_tune(model,factory,rounds=128):
    """Exactly equal HQ budget for each compared initial/trained actor; never consumes held-out maps."""
    validate_factory(factory);env=MissionEnv(scenario_factory=factory);env.reset(TRAIN_SEEDS[0]);teacher=MissionTeacher();rows=[]
    active=None
    for turn in range(rounds):
        controlled=('A','B')[(turn//32)%2];other='B' if controlled=='A' else 'A'
        if active!=turn//32:
            if rows:rows[-1]['terminal']=True
            env.reset(TRAIN_SEEDS[(turn//32)%len(TRAIN_SEEDS)],options={'swap':bool((turn//64)%2)});active=turn//32
        before=env.engine.world.tick;last=None
        while env.agents and env.engine.world.tick==before:
            actions={other:env.heuristic(other)}
            if not env.finished[controlled]:
                x=env.vector(controlled);mask=env.mask(controlled);action,value,lp=choose(model,x,mask);row=dict(obs=x.copy(),mask=mask.copy(),action=action,value=value,logp=lp,reward=0.,start=turn%32==0 and last is None,terminal=False,advance=False);rows.append(row);last=row;actions[controlled]=action
            _,reward,_,_,_=env.step(actions)
        if last:last.update(reward=reward[controlled],terminal=not bool(env.agents),advance=True)
        if not env.agents:env.reset(TRAIN_SEEDS[(turn+1)%len(TRAIN_SEEDS)])
        if (turn+1)%64==0:update(model,rows,choose(model,env.vector(controlled),env.mask(controlled),deterministic=True)[1],teacher);rows=[]
    if rows:update(model,rows,choose(model,env.vector('A'),env.mask('A'),deterministic=True)[1],teacher)
    return dict(hq_rounds=rounds,teacher_calls=0,held_out_experience=False)
