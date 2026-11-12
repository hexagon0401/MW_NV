"""Reproducible headless workload; never touches training data or remote services."""
import argparse,cProfile,io,json,pstats,time,resource
from .candidate_env import CandidateEnv

def workload(seed=19,rounds=24):
    env=CandidateEnv(decision_seconds=10);env.reset(seed);started=time.perf_counter()
    for _ in range(rounds):
        tick=env.engine.world.tick
        while env.agents and env.engine.world.tick==tick:
            env.step({a:env.heuristic(a) for a in env.agents if not env.finished[a]})
        if not env.agents:break
    elapsed=time.perf_counter()-started
    return dict(seed=seed,rounds=rounds,sim_seconds=env.engine.world.tick*.2,elapsed_seconds=elapsed,
                sim_speed=env.engine.world.tick*.2/elapsed,hash=env.engine.world.checksum(),rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--rounds',type=int,default=24);a=p.parse_args()
    profile=cProfile.Profile();profile.enable();result=workload(rounds=a.rounds);profile.disable()
    out=io.StringIO();pstats.Stats(profile,stream=out).sort_stats('cumulative').print_stats(15);result['profile']=out.getvalue()
    from pathlib import Path
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='profile'})
if __name__=='__main__':main()
