"""Bounded representative idle/moving workloads; Linux RSS is KiB."""
import json,time,resource,platform
from pathlib import Path
from .scenario import create_release_match
from .runtime import Engine
from .types import Team,WorldPos,Vehicle
from .catalog import make_soldier


def benchmark(count,ticks=100):
    w=create_release_match(5);w.soldiers.clear();w.squads.clear();w.vehicles.clear()
    for i in range(count):
        team=Team(i%2);index=i//2
        x=10000+(index%16)*200;y=10000+(index//16)*200
        w.soldiers[i+1]=make_soldier(i+1,team,WorldPos(x if team==Team.A else 102400-x,y))
    w.soldiers[1].pos=WorldPos(10000,8000);w.soldiers[2].pos=WorldPos(92400,8000)
    for i in range(10):w.vehicles[10000+i]=Vehicle(10000+i,Team(i%2),WorldPos(40000+i*1000,60000))
    e=Engine(w)
    for team,id in ((0,1),(1,2)):
        s=w.soldiers[id];e.submit(dict(cmd_id=1,team=team,op=2,unit=id,arg0=400 if team==0 else 624,arg1=80,ttl=3000))
    start=time.perf_counter();e.step(ticks/5);elapsed=time.perf_counter()-start
    assert all(s=='RUNNING' for s in w.queue.status.values())
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return dict(entities=count,ticks=ticks,ticks_per_second=ticks/elapsed,max_rss_mb=rss/(1024*1024 if platform.system()=='Darwin' else 1024),sample_wall_time_s=elapsed,vehicles=10,workload='idle troops + 2 continuously moving infantry + 10 idle vehicles',platform=platform.platform())


if __name__=='__main__':
    results=[benchmark(n) for n in (100,300,500)]
    print(json.dumps(results,indent=2))
    Path('examples/benchmark.json').write_text(json.dumps(results,indent=2)+'\n')
