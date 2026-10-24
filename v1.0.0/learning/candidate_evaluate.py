"""Held-out paired-side evaluation; modes and policy contracts stay separate."""
import argparse,json,uuid
from pathlib import Path
import numpy as np
from .candidate_env import CandidateEnv
from .candidate_policy import CandidatePolicy
from .results import record_world
from engine.objectives import summary


def evaluate(seed=10000,policy='rules',opponent='rules',swap=False,db='data/results.sqlite'):
    if not 10000<=seed<=10099:raise ValueError('held-out seed must be 10000..10099')
    env=CandidateEnv();env.reset(seed);rng=np.random.default_rng(seed)
    assigned={'A':opponent if swap else policy,'B':policy if swap else opponent}
    models={a:None if p in ('rules','random') else CandidatePolicy(p) for a,p in assigned.items()}
    names={a:m.policy_id if m else p for a,p in assigned.items() for m in [models[a]]}
    while env.agents:
        actions={}
        for a,p in assigned.items():
            m=models[a];actions[a]=m.predict(env.vector(a),env.mask(a)) if m else int(rng.choice(np.flatnonzero(env.mask(a)))) if p=='random' else env.heuristic(a)
        env.step(actions)
    w=env.engine.world
    if db:record_world(db,w,'evaluation',names)
    return dict(summary(w),policies=names,swapped=swap)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=10000);p.add_argument('--count',type=int,default=1);p.add_argument('--policy',default='rules');p.add_argument('--opponent',default='rules');p.add_argument('--db',default='data/results.sqlite');p.add_argument('--output',default='data/candidate-evaluation.json');a=p.parse_args()
    if a.count<1 or a.start<10000 or a.start+a.count>10100:p.error('held-out range 10000..10099 required')
    results=[]
    for seed in range(a.start,a.start+a.count):
        for swapped in (False,True):
            result=evaluate(seed,a.policy,a.opponent,swapped,a.db);results.append(result);print(json.dumps(result),flush=True)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(results,indent=2)+'\n')
