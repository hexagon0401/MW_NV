"""Run local rule-HQ matches: python -m engine.headless --seeds 10."""
import argparse,json
from pathlib import Path
from agents.rule_hq import RuleHQ
from .runtime import Engine
from .scenario import create_match,create_release_match
from .types import Team
from .orders import OrderError
from .objectives import summary


def run_match(seed=0,swap=False,release=False,stats=None):
    e=Engine((create_release_match if release else create_match)(seed,swap));policies={t:RuleHQ() for t in Team}
    while not getattr(e.world,'ended',False):
        # Both policies see snapshots from the same simulation tick.
        observations={t:e.observe(t) for t in Team}
        for t in Team:
            for command in policies[t].observe_and_issue(observations[t]):
                try:e.submit_for(t,command)
                except OrderError:pass  # rejection remains in the event log
        e.step(30)
    result=summary(e.world)
    result.update(swapped=swap,captures=sum(x['event_kind']=='OBJECTIVE_CAPTURED' for x in e.world.events),
                  invalid_commands=sum(x['event_kind']=='ORDER_REJECTED' for x in e.world.events),
                  attacks=sum(x['event_kind']=='ABSTRACT_ATTACK' for x in e.world.events))
    if stats:
        from learning.results import record_world
        record_world(stats,e.world,'rules',{'A':'algorithm','B':'algorithm'})
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seeds',type=int,default=10)
    parser.add_argument('--swap',action='store_true');parser.add_argument('--output',type=Path)
    parser.add_argument("--paired",action="store_true",help="run both side assignments for each seed")
    parser.add_argument("--release",action="store_true",help="use the 1024m release map")
    args=parser.parse_args()
    if args.seeds<1:parser.error('--seeds must be positive')
    results=[dict(seed=seed,normal=run_match(seed,release=args.release),swapped=run_match(seed,True,args.release)) for seed in range(args.seeds)] if args.paired else [run_match(seed,args.swap,args.release) for seed in range(args.seeds)]
    output=json.dumps(results,indent=2)+'\n'
    if args.output:args.output.write_text(output)
    else:print(output)


if __name__=='__main__':main()
