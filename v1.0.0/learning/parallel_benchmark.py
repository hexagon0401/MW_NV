"""Small equal-command process scaling experiment; no PPO or network mutation."""
import argparse,json,time,os
from pathlib import Path
from .process_env import ProcessEnv

def measure(count,rounds):
    workers=[ProcessEnv('legacy') for _ in range(count)];packets=[]
    try:
        info=dict(descriptor=dict(seed=4,family=3,swap=False),assignments={'A':'algorithm','B':'algorithm'},generation=0,episode=0,active=True)
        for w in workers:packets.append(w.call('reset',dict(info)))
        def cpu():return sum(sum(map(int,Path(f'/proc/{w.process.pid}/stat').read_text().split()[13:15]))/os.sysconf('SC_CLK_TCK') for w in workers)
        cpu_before=cpu();started=time.perf_counter()
        for _ in range(rounds):
            before=[p['tick'] for p in packets];pending=set(range(count))
            while pending:
                for i in sorted(pending):workers[i].send('step',({a:packets[i]['heuristic'][a] for a in ('A','B') if not packets[i]['finished'][a]},0))
                for i in sorted(pending):packets[i]=workers[i].receive()
                pending={i for i in pending if packets[i]['tick']==before[i] and not packets[i]['ended']}
        elapsed=time.perf_counter()-started;cpu_seconds=cpu()-cpu_before
        hashes=[w.call('snapshot')['environment']['world'].checksum() for w in workers]
        rss=0
        for w in workers:
            for line in Path(f'/proc/{w.process.pid}/status').read_text().splitlines():
                if line.startswith('VmRSS:'):rss+=int(line.split()[1])
        return dict(workers=count,rounds=rounds,sim_seconds=sum(p['tick']*.2 for p in packets),wall_seconds=elapsed,aggregate_speed=sum(p['tick']*.2 for p in packets)/elapsed,worker_rss_kib=rss,cpu_seconds=cpu_seconds,cpu_cores_average=cpu_seconds/elapsed,hashes=hashes)
    finally:
        for w in workers:w.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--rounds',type=int,default=12);a=p.parse_args()
    result=[measure(i,a.rounds) for i in (1,2,3)];Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print([{k:v for k,v in x.items() if k!='hashes'} for x in result])
