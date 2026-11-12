"""Local model-driven matches; recorded commands replay without model calls."""
import argparse,json
from pathlib import Path
from .replay import RecordingEngine
from .scenario import create_release_match
from .types import Team
from .viewer_export import frame,export_view
from agents.local_hq import issue_hq_round
from agents.hybrid_hq import HybridHQ


def run(seed=0,endpoint='http://127.0.0.1:8080/v1',model='local',rounds=100,output='data/local'):
    e=RecordingEngine(create_release_match(seed));initial=frame(e.world)
    policies={t:HybridHQ(endpoint,model=model) for t in Team}
    for _ in range(rounds):
        if getattr(e.world,'ended',False):break
        issue_hq_round(e,policies);e.step(30)
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
    path.with_suffix('.replay.json').write_text(json.dumps(e.document()))
    if getattr(e.world,'ended',False):
        path.with_suffix('.view.json').write_text(json.dumps(export_view(e,initial)))
        from learning.results import record_world
        record_world(path.parent/'results.sqlite',e.world,'hybrid',{('A' if t==0 else 'B'):'llm:'+model+'/'+p.last_decision.get('policy','algorithm') for t,p in policies.items()})
    return e


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--endpoint',default='http://127.0.0.1:8080/v1');p.add_argument('--model',default='local');p.add_argument('--seed',type=int,default=0);p.add_argument('--rounds',type=int,default=100);p.add_argument('--output',default='data/local');a=p.parse_args()
    e=run(a.seed,a.endpoint,a.model,a.rounds,a.output)
    events=[x for x in e.world.events if x['event_kind']=='HQ_DECISION']
    print(json.dumps(dict(ticks=e.world.tick,ended=getattr(e.world,'ended',False),decisions=len(events),fallbacks=sum(x['payload']['metadata']['source']!='llm' for x in events))))
