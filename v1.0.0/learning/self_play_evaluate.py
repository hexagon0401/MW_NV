"""Frozen held-out PPO vs champion and hybrid vs champion; never creates teacher labels."""
import json,time,os
from pathlib import Path
from .candidate_evaluate import evaluate as ppo_evaluate
from .self_play import current
from .training_maps import training_scenario
from .results import record_world
from agents.hybrid_hq import HybridHQ
from agents.local_hq import issue_hq_round
from engine.runtime import Engine
from engine.objectives import summary
from engine.types import Team

def evaluate(root,generation):
    root=Path(root);policy=str(current(root)/'latest.npz');champion=str(root/'champion.npz');output=[]
    for seed in range(10000,10005):
        for swapped in (False,True):
            result=ppo_evaluate(seed,policy,champion,swapped,terrain_variants=True);output.append(dict(result,mode='evaluation'))
            engine=Engine(training_scenario(seed));policies={t:HybridHQ('https://integrate.api.nvidia.com/v1',model='nvidia/nemotron-3.5-lightning-30b-a3b',timeout=30,api_key=os.environ.get('NVIDIA_API_KEY_A' if (int(t)+seed%2)%2==0 else 'NVIDIA_API_KEY_B'),policy=policy if int(t)==int(swapped) else champion) for t in Team}
            failures=0
            while not getattr(engine.world,'ended',False):
                issue_hq_round(engine,policies);failures+=sum(p.last_decision['source']!='llm' for p in policies.values());engine.step(30)
            record_world('data/results.sqlite',engine.world,'hybrid',{a:policies[t].tactical.model.policy_id if policies[t].tactical.model else 'algorithm' for t,a in [(Team.A,'A'),(Team.B,'B')]})
            output.append(dict(summary(engine.world),mode='hybrid',swapped=swapped,learner_team='B' if swapped else 'A',key_rotation=seed%2,fallback_decisions=failures))
            (root/'evaluation.json').write_text(json.dumps(dict(generation=generation,results=output,complete=False)))
    (root/'evaluation.json').write_text(json.dumps(dict(generation=generation,results=output,complete=True)))
    return output
