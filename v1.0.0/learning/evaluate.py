"""Seeded full-episode evaluation with comparable action budgets."""
import json,hashlib,time
from pathlib import Path
import numpy as np
from .env import HQEnv
from .policies import choose,NumpyPolicy


def evaluate(seed,policy='rules',opponent='rules'):
    env=HQEnv();env.reset(seed=seed);rng=np.random.default_rng(seed)
    learner=NumpyPolicy(policy) if policy not in ('rules','random') else None
    old=NumpyPolicy(opponent) if opponent not in ('rules','random') else None
    invalid=0;start=time.perf_counter()
    while env.agents:
        actions={}
        for a,name,model in [('A',policy,learner),('B',opponent,old)]:
            actions[a]=model.predict(env.vector(a),env.mask(a)) if model else choose(env,a,rng if name=='random' else None)
        _,_,_,_,info=env.step(actions);invalid+=sum(i.get('invalid_action',False) for i in info.values())
    w=env.engine.world
    return dict(match_id=hashlib.sha256(f'{seed}:{policy}:{opponent}'.encode()).hexdigest()[:16],seed=seed,policy=str(policy),opponent=str(opponent),winner=None if w.winner is None else int(w.winner),scores=[w.teams[t].score for t in (0,1)],unit_losses=[sum(not s.alive for s in w.soldiers.values() if s.team==t) for t in (0,1)],supply_remaining=[w.teams[t].supply for t in (0,1)],invalid_actions=invalid,ticks=w.tick,wall_time_s=time.perf_counter()-start)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=50);p.add_argument('--start',type=int,default=1000);p.add_argument('--policy',default='rules');p.add_argument('--opponent',default='rules');p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    records=[evaluate(s,args.policy,args.opponent) for s in range(args.start,args.start+args.count)]
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(records,indent=2)+'\n')
    print(f'{len(records)} matches completed, invalid actions={sum(r["invalid_actions"] for r in records)}')
