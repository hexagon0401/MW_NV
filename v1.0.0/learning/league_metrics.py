"""Observable tactical opportunity/selection fingerprints; no causal storytelling."""
from collections import Counter
import json,hashlib
from .results import records

def new_metrics():return {a:dict(opportunities={},selected={},commands=[]) for a in ('A','B')}

def opportunity(metrics,team,items):
    counter=metrics[team]['opportunities']
    for role in sorted({c['role']+':'+c.get('analysis',{}).get('tactic','direct') for c in items}):counter[role]=counter.get(role,0)+1

def selection(metrics,team,candidate,tick):
    role=candidate['role']+':'+candidate.get('analysis',{}).get('tactic','direct');counter=metrics[team]['selected'];counter[role]=counter.get(role,0)+1
    metrics[team]['commands'].append(dict(role=role,unit=candidate['command']['unit'],op=candidate['command']['op'],target=candidate['command']['target'],tick=tick,cmd_id=tick*100+sum(r['tick']==tick for r in metrics[team]['commands'])+1))

def finish(metrics,world,initial=None):
    from .tactical_patterns import detect
    accepted={(e['payload'].get('team'),e['payload'].get('cmd_id')) for e in world.events if e['event_kind']=='ORDER_ACCEPTED'}
    patterns=detect(world,{a:[c for c in v['commands'] if (('A','B').index(a),c.get('cmd_id')) in accepted] for a,v in metrics.items()},initial)
    counts=Counter(e['event_kind'] for e in world.events);failures=Counter(e['payload'].get('reason','unknown') for e in world.events if e['event_kind']=='ORDER_FAILED')
    for team in ('A','B'):
        rows=metrics[team]['commands'];accepted=[e for e in world.events if e['event_kind']=='ORDER_ACCEPTED' and e['payload'].get('team')==('A','B').index(team)]
        ids={e['payload']['cmd_id'] for e in accepted};outcomes=Counter(e['event_kind'] for e in world.events if e['payload'].get('team')==('A','B').index(team) and e['payload'].get('cmd_id') in ids)
        metrics[team]['order_outcomes']=dict(outcomes)
        role_by_id={r['cmd_id']:r['role'] for r in rows};role_outcomes={}
        for e in world.events:
            p=e['payload'];role=role_by_id.get(p.get('cmd_id'))
            if p.get('team')!=('A','B').index(team) or role is None or e['event_kind'] not in ('ORDER_ACCEPTED','ORDER_COMPLETED','ORDER_FAILED','ORDER_CANCELLED'):continue
            counter=role_outcomes.setdefault(role,{});counter[e['event_kind']]=counter.get(e['event_kind'],0)+1
        metrics[team]['role_outcomes']=role_outcomes
        metrics[team]['phases']={phase:dict(Counter(r['role'] for r in rows if low<=r['tick']*.2<high)) for phase,low,high in [('early',0,300),('middle',300,900),('late',900,float('inf'))]}
        # Bounded examples; aggregate counts and opportunity denominators remain complete.
        metrics[team]['commands']=rows[:3]+rows[-3:] if len(rows)>6 else rows
    return dict(teams=metrics,events=dict(counts),failures=dict(failures),friendly_damage=sum(e['payload'].get('damage',0) for e in world.events if e['event_kind']=='UNIT_DAMAGED' and e['payload'].get('friendly_fire')),sequences=patterns,detector_version='league-fingerprint-1')

def document(db='data/results.sqlite'):
    rows=sorted([r for r in records(db,'match') if r.get('league')],key=lambda r:(r.get('created_at',''),r['id']))
    runs={}
    for row in rows:
        league=row['league'];run=runs.setdefault(league['run'],dict(run=league['run'],rules_version=row['rules_version'],matches=0,learners={}))
        if row['mode']!='training':continue
        run['matches']+=1
        for team,learner in league['assignments'].items():
            if learner not in ('PPO1','PPO2'):continue
            values=run['learners'].setdefault(learner,dict(games=0,wins=0,losses=0,draws=0,opportunities={},selected={},recent=[]));values['games']+=1
            outcome='draws' if row['winner'] is None else 'wins' if row['winner']==('A','B').index(team) else 'losses';values[outcome]+=1
            values['recent'].append(dict(match=row['id'],outcome=outcome,score=row['scores'],team=team,swapped=row['swapped'],policies=row['policies'],objectives=row.get('objective_stats'),fingerprint=league.get('metrics',{}).get('teams',{}).get(team)))
            for key in ('opportunities','selected'):
                for role,count in league.get('metrics',{}).get('teams',{}).get(team,{}).get(key,{}).items():values[key][role]=values[key].get(role,0)+count
    for run in runs.values():
        for learner in run['learners'].values():learner['win_rate']=learner['wins']/max(1,learner['games']);learner['recent']=learner['recent'][-100:]
    return dict(schema=1,evidence='observed_change_only',runs=list(runs.values()),causal_claim=False)
