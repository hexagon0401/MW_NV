"""CPU-bounded NIM-only demonstrations, isolated from PPO trajectories and counters."""
import argparse,gzip,json,os,signal,time
from pathlib import Path
from types import SimpleNamespace
from engine.replay import encode,decode
from engine.runtime import Engine
from engine.multi_scenario import create
from engine.orders import OrderError
from engine.viewer_export import frame
from agents.mission_tactics import candidates,commands
from agents.tactics import compatible
from .mission_env import MissionTeacher
from .nim_budget import PairLease
from .self_play import atomic_json


def run(directory,cpu_seconds=10,clients=None,budget_root='data/nim-budget'):
    directory=Path(directory);job=json.loads((directory/'job.json').read_text());checkpoint=directory/'world.json.gz'
    w=decode(json.loads(gzip.decompress(checkpoint.read_bytes()))) if checkpoint.exists() else create(job['seed'],swap=job['swap'],scenario_id=job['scenario_id'])
    if w.rules_version!='combined-arms-6':raise ValueError('incompatible demonstration checkpoint')
    if 10000<=w.seed<10100 or 20000<=w.seed<20100:raise ValueError('held-out seed cannot be coached')
    e=Engine(w);teacher=MissionTeacher();samples=directory/'samples.npz'
    if samples.exists():teacher.load(samples)
    progress_path=directory/'progress.json'
    if progress_path.exists():teacher.stats.update(json.loads(progress_path.read_text()).get('teacher',{}))
    stage_events=json.loads(progress_path.read_text()).get('stage_events',{}) if progress_path.exists() else {}
    initial_path=directory/'initial.json'
    if not initial_path.exists():atomic_json(initial_path,frame(w))
    initial=json.loads(initial_path.read_text());start=time.process_time();stopped=[False];old={}
    for sig in (signal.SIGTERM,signal.SIGINT):old[sig]=signal.signal(sig,lambda *_:stopped.__setitem__(0,True))
    try:
        while not stopped[0] and time.process_time()-start<cpu_seconds and not getattr(w,'ended',False):
            if w.tick%150:
                while w.tick%150 and not getattr(w,'ended',False) and not stopped[0] and time.process_time()-start<cpu_seconds:e.step(.2)
                if w.tick%150:break
            observations={a:e.observe(i) for i,a in enumerate(('A','B'))};items={a:candidates(observations[a]) for a in ('A','B')}
            frozen=SimpleNamespace(items=items,raw=lambda a:observations[a],teacher_source=job['kind'])
            batches=None
            if w.tick%150==0:
                lease=PairLease(budget_root,'demonstration')
                with lease as admitted:
                    if admitted:
                        teacher.collect(frozen,clients=clients);batches=getattr(teacher,'last_batches',None);lease.defer(teacher.stats.get('retry_in_seconds',0))
            # No delayed answer is ever applied to a later observation.
            chosen={}
            for a in ('A','B'):
                if batches is not None:chosen[a]=batches[('A','B').index(a)]
                else:
                    selected=[]
                    for _ in range(4):
                        available=compatible(items[a],selected)
                        if not available:break
                        selected.append(max(available,key=lambda c:(c['score'],-c['id'])))
                    chosen[a]=selected
            before=len(w.events)
            for i,a in enumerate(('A','B')):
                for c in commands(observations[a],chosen[a]):
                    try:e.submit_for(i,c)
                    except OrderError:pass
            # Check CPU at every physical tick; preserve command state on exhaustion.
            boundary=w.tick+150-w.tick%150
            while w.tick<boundary and not getattr(w,'ended',False) and not stopped[0] and time.process_time()-start<cpu_seconds:e.step(.2)
            outcome={}
            for event in w.events[before:]:
                kind=event['event_kind']
                if kind in ('UNIT_RESUPPLIED','DISEMBARK_DONE','BUILDING_ENTERED','FLAG_STOLEN','FLAG_PICKED_UP','FLAG_RETURNED'):outcome[kind]=outcome.get(kind,0)+1
            # Keep failures too. Labels remain tied to their original decision tick.
            for row in teacher.rows:
                if len(row)>4 and row[4].get('tick')==observations['A']['tick']:row[4]['outcome']=outcome
            for name,count in outcome.items():stage_events[name]=stage_events.get(name,0)+count
            missing={}
            for a in ('A','B'):
                roles={c['role'] for c in items[a]};need_supply=any(u['alive'] and u.get('ammo')==0 and observations[a]['catalog']['units'][u['type_id']]['ammo'] for u in observations[a]['units'])
                missing[a]=(['supply'] if need_supply and 'supply' not in roles else [])+(['infiltrate_or_flag'] if w.mode=='capture_flag' and not roles.intersection(('infiltrate','flag','return','recover')) else [])
            atomic_json(directory/'progress.json',dict(tick=w.tick,scenario_id=job['scenario_id'],kind=job['kind'],paired=teacher.stats['paired'],samples=len(teacher.rows),teacher=dict(teacher.stats),ended=bool(getattr(w,'ended',False)),cpu_seconds=time.process_time(),last_outcome=outcome,stage_events=stage_events,candidate_missing=missing))
            # Continue pending physical commands after a CPU-budget pause rather than
            # resubmitting them. Saved queue/RNG are authoritative on the next slice.
            if w.tick<boundary:break
    finally:
        payload=gzip.compress(json.dumps(encode(w),separators=(',',':')).encode(),compresslevel=1)
        tmp=checkpoint.with_suffix('.partial');tmp.write_bytes(payload);tmp.replace(checkpoint)
        temporary=directory/'samples.partial.npz';teacher.save(temporary);temporary.replace(samples)
        if getattr(w,'ended',False):
            from .results import record_world
            record_world('data/results.sqlite',w,job['kind'],{'A':'NIM-teacher-with-algorithm-fallback','B':'NIM-teacher-with-algorithm-fallback'},match_id=job.get('run_id','coach')+'-'+job['id'],initial_frame=initial,metadata=dict(coaching=job))
        atomic_json(directory/'slice.json',dict(cpu_seconds=time.process_time(),tick=w.tick,ended=bool(getattr(w,'ended',False)),paired=teacher.stats['paired'],samples=len(teacher.rows)))
        for sig,handler in old.items():signal.signal(sig,handler)
    return w

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',required=True);p.add_argument('--cpu-seconds',type=float,default=10);a=p.parse_args();run(a.directory,a.cpu_seconds)
