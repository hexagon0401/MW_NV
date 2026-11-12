"""Unpaced release-game diagnostics with bounded per-match persisted reports."""
import argparse,json,time
from collections import Counter
from pathlib import Path
from .runtime import Engine
from .scenario import create_release_match
from .objectives import summary
from .orders import OrderError
from agents.tactics import TacticalHQ


def run(seed,swap):
    e=Engine(create_release_match(seed,swap));w=e.world;hq={t:TacticalHQ() for t in (0,1)};start=time.perf_counter();errors=[]
    while not getattr(w,'ended',False):
        obs={t:e.observe(t) for t in (0,1)}
        for t in (0,1):
            for c in hq[t].observe_and_issue(obs[t]):
                try:e.submit_for(t,c)
                except OrderError as exc:errors.append(str(exc))
        e.step(30)
    counts=Counter(ev['event_kind'] for ev in w.events);failures=Counter(ev['payload'].get('reason','UNKNOWN') for ev in w.events if ev['event_kind']=='ORDER_FAILED')
    invalid=[]
    for u in [*w.soldiers.values(),*w.vehicles.values()]:
        if not w.terrain.inside(u.pos.x_cm,u.pos.y_cm) or u.hp<0:invalid.append(u.id)
        if u.id in w.soldiers and u.carrier_id is not None and (u.carrier_id not in w.vehicles or u.id not in w.vehicles[u.carrier_id].passenger_ids):invalid.append(u.id)
    for v in w.vehicles.values():
        if len(v.passenger_ids)>w.vehicle_specs[v.type_id]['capacity'] or len(v.passenger_ids)!=len(set(v.passenger_ids)):invalid.append(v.id)
    moved={ev['payload']['unit'] for ev in w.events if ev['event_kind']=='UNIT_MOVED'}
    attacks=Counter();failed_ops=Counter()
    for ev in w.events:
        p=ev['payload']
        if ev['event_kind']=='ABSTRACT_ATTACK':attacks[(w.soldiers.get(p['unit']) or w.vehicles[p['unit']]).type_id]+=1
        if ev['event_kind']=='ORDER_FAILED':
            c=w.queue.commands[f"{p['team']}:{p['cmd_id']}"];failed_ops[f'{c.op.name}:{p.get("reason")}']+=1
    wall=time.perf_counter()-start
    return dict(summary(w),swap=swap,hq='algorithm (no LLM)',wall_seconds=round(wall,3),speedup=round(w.tick/5/wall,2),events=dict(counts),failures=dict(failures),failed_ops=dict(failed_ops),rejections=errors,invariant_errors=invalid,attacks_by_type=dict(attacks),stationary_alive=[u.id for u in [*w.soldiers.values(),*w.vehicles.values()] if u.alive and u.id not in moved],survivors={str(t):dict(infantry=sum(s.alive and s.team==t for s in w.soldiers.values()),vehicles=sum(v.alive and v.team==t for v in w.vehicles.values())) for t in (0,1)})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='docs/visual-refresh/ten-games.json');a=p.parse_args();path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);results=[]
    for seed in range(5):
        for swap in (False,True):
            result=run(seed,swap);results.append(result);path.write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('seed','swap','winner','scores','wall_seconds','failures','invariant_errors')}),flush=True)
