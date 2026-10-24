"""Bounded holdout evaluation. No promotion based on training rewards."""
import csv,json,statistics,hashlib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from .evaluate import evaluate


def task(args):return evaluate(*args)


def run():
    root=Path('data/policies');required=[root/f'policy{i}.npz' for i in range(3)]
    if not all(p.exists() for p in required):raise ValueError('train the three-policy pool first')
    jobs=[(s,p,'rules') for p in ('rules',str(required[0]),str(required[2])) for s in range(10000,10100)]
    jobs += [(s,str(required[2]),str(p)) for p in required[:2] for s in range(10000,10010)]
    records=[]
    with ProcessPoolExecutor(max_workers=3) as executor:
        futures=[executor.submit(task,j) for j in jobs]
        for future in as_completed(futures):
            records.append(future.result())
            if len(records)%10==0:print(f'holdout matches {len(records)}/{len(jobs)}',flush=True)
    records.sort(key=lambda r:(r['policy'],r['opponent'],r['seed']))
    output=Path('examples/holdout_evaluation.json');output.write_text(json.dumps(records,indent=2)+'\n')
    with Path('examples/holdout_evaluation.csv').open('w') as file:
        writer=csv.DictWriter(file,fieldnames=records[0].keys());writer.writeheader();writer.writerows(records)
    groups={}
    for r in records:groups.setdefault((r['policy'],r['opponent']),[]).append(r)
    lines=['# Held-out evaluation','', 'Training seeds: 0–49. Baselines: 1000–1049. Holdout: 10000–10099.', '', '| Policy | Opponent | Games | A wins | Draws | Mean score difference | Invalid actions |','|---|---|---:|---:|---:|---:|---:|']
    for (policy,opponent),rows in groups.items():
        lines.append(f'| {policy} | {opponent} | {len(rows)} | {sum(r["winner"]==0 for r in rows)} | {sum(r["winner"] is None for r in rows)} | {statistics.mean(r["scores"][0]-r["scores"][1] for r in rows):.2f} | {sum(r["invalid_actions"] for r in rows)} |')
    lines += ['', 'Each policy receives one squad/goal action per HQ round. No LLM calls.', 'These are small CPU training runs; no policy improvement is assumed.', 'Detailed losses, supply remaining and measured wall time are in the CSV/JSON.']
    Path('examples/EVALUATION.md').write_text('\n'.join(lines)+'\n')
    pool=json.loads((root/'pool.json').read_text());pool['holdout_complete']=True
    mean=lambda name:statistics.mean(r['scores'][0]-r['scores'][1] for r in groups[(name,'rules')])
    candidates=['rules',str(required[0]),str(required[2])];best=max(candidates,key=mean)
    pool['best']=best;pool['selection']='maximum held-out mean score difference; rules wins ties';pool['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in required}
    (root/'pool.json').write_text(json.dumps(pool,indent=2)+'\n')
    Path('examples/policy_pool.json').write_text(json.dumps(pool,indent=2)+'\n')
    print('Evaluation and conservative policy selection complete',flush=True)


if __name__=='__main__':run()
