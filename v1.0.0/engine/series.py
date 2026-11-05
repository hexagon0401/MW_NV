"""Explicitly started repeat matches; one durable summary per completed match."""
import argparse,json
from pathlib import Path
from .headless import run_match


def run(output='data/series.jsonl',count=1):
    if count<0:raise ValueError('count >= 0 required')
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
    seed=sum(1 for line in path.open() if line.strip()) if path.exists() else 0
    completed=0
    try:
        while count==0 or completed<count:
            result=run_match(seed,swap=bool(seed%2),release=True,stats=path.parent/'results.sqlite')
            with path.open('a') as stream:stream.write(json.dumps(result)+'\n');stream.flush()
            print(json.dumps(result),flush=True);seed+=1;completed+=1
    except KeyboardInterrupt:print('Stopped; completed matches retained.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=1,help='0 repeats until Ctrl+C');p.add_argument('--output',default='data/series.jsonl');a=p.parse_args();run(a.output,a.count)
