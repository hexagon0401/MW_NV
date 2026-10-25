"""Ten headless held-out engine audits; no teacher or training updates."""
import json,time
from pathlib import Path
from collections import Counter,defaultdict
from learning.candidate_env import CandidateEnv
from learning.results import record_world
from engine.viewer_export import export_view,frame


def run():
    output=Path('docs/tactical-redesign');output.mkdir(parents=True,exist_ok=True);results=[];started=time.monotonic();first=None
    for seed in range(20000,20005):
        for swap in (False,True):
            env=CandidateEnv();env.reset(seed,options={'swap':swap});initial=frame(env.engine.world);actions=[];positions={};stalls=defaultdict(int);maximum=defaultdict(int);before=time.monotonic()
            while env.agents:
                action={a:env.heuristic(a) for a in env.agents};actions.append(action);tick=env.engine.world.tick;env.step(action)
                w=env.engine.world
                if w.tick!=tick:
                    for u in [*w.soldiers.values(),*w.vehicles.values()]:
                        p=(u.pos.x_cm,u.pos.y_cm)
                        if u.alive and getattr(u,'carrier_id',None) is None and u.task_state in ('MOVING','PATH_PENDING','PATHING','WAITING_TRAFFIC','WAITING_PASSENGERS','BOARDING_QUEUE') and positions.get(u.id)==p:stalls[u.id]+=w.tick-tick
                        else:stalls[u.id]=0
                        maximum[u.id]=max(maximum[u.id],stalls[u.id]);positions[u.id]=p
                if len(actions)>20000:raise RuntimeError('HQ decision loop did not terminate')
            events=w.events;counts=Counter(e['event_kind'] for e in events);failures=Counter(str(e['payload'].get('reason','unknown')) for e in events if e['event_kind']=='ORDER_FAILED');damage=[e['payload'] for e in events if e['event_kind']=='UNIT_DAMAGED'];shots=[e['payload'] for e in events if e['event_kind']=='ABSTRACT_ATTACK']
            result=dict(seed=seed,swapped=swap,winner=None if w.winner is None else int(w.winner),scores=[w.teams[t].score for t in (0,1)],sim_seconds=w.tick*.2,wall_seconds=round(time.monotonic()-before,2),checksum=w.checksum(),shots=len(shots),hits=sum(bool(s['hit']) for s in shots),tank_impacts=counts['TANK_IMPACT'],artillery_impacts=counts['ARTILLERY_IMPACT'],splash_damage=sum(d['damage'] for d in damage if d.get('cause')=='tank_splash'),friendly_damage=sum(d['damage'] for d in damage if d.get('friendly_fire')),order_failures=dict(failures),traffic_waits=counts['VEHICLE_WAITING'],events=dict(counts),stationary_120s=[dict(unit=uid,seconds=ticks*.2) for uid,ticks in sorted(maximum.items(),key=lambda x:-x[1])[:10] if ticks>=600],living={str(t):dict(infantry=sum(u.alive and u.team==t for u in w.soldiers.values()),vehicles=sum(u.alive and u.team==t for u in w.vehicles.values())) for t in (0,1)})
            results.append(result);record_world('data/results.sqlite',w,'evaluation',{'A':'rules3-audit','B':'rules3-audit'},match_id=f't05-audit-fixed-{seed}-{int(swap)}')
            (output/'games.json').write_text(json.dumps(dict(complete=False,mode='algorithm evaluation; no PPO/NIM',results=results),indent=2))
            print(json.dumps({k:result[k] for k in ('seed','swapped','winner','scores','sim_seconds','wall_seconds','tank_impacts','friendly_damage')}),flush=True)
            if first is None:first=(seed,swap,actions,w.checksum())
            # The latest audit is saved locally for VFX/browser review, not published as a learning match.
            if len(results)==10:Path('data/t05-audit-view.json').write_text(json.dumps(export_view(env.engine,initial),separators=(',',':')))
    seed,swap,actions,checksum=first;env=CandidateEnv();env.reset(seed,options={'swap':swap})
    for action in actions:env.step(action)
    assert env.engine.world.checksum()==checksum,'same-seed/action replay diverged'
    doc=dict(complete=True,mode='algorithm evaluation; no PPO/NIM',rules_version='combined-arms-3',map_id='river-districts',map_version='2',deterministic_reexecution=True,total_wall_seconds=round(time.monotonic()-started,2),results=results)
    (output/'games.json').write_text(json.dumps(doc,indent=2));print('TEN_GAMES_AND_DETERMINISTIC_REEXECUTION_PASS',flush=True)

if __name__=='__main__':run()
