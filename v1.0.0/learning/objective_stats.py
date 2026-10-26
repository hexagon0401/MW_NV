"""Read-only first-capture races and ownership history. No inference from final ownership."""
from itertools import combinations

NAMES={'201':'북부 통신','202':'중앙 광장','203':'남부 보급창'}
FILTERS=('mode','rules_version','catalog_version','map_id','map_version','map_family','swapped','policy_a','policy_b')

def collect(world,initial=None):
    if initial is None or initial.get('tick')!=0:
        return dict(schema=1,available=False,reason='complete_initial_state_unavailable')
    facilities={str(f['id']):f for f in initial.get('facilities',[]) if f.get('kind')=='OBJECTIVE'}
    if not facilities:return dict(schema=1,available=False,reason='no_objective_initial_state')
    tick_s=world.config.tick_s;end=world.tick*tick_s;points={};last={};owners={}
    for id,f in facilities.items():
        owner=f.get('owner');owners[id]=owner;last[id]=0.
        points[id]=dict(initial_owner=owner,first_team=None,first_at_s=None,lost_after_first=False,first_lost_at_s=None,regained_by_first=False,opponent_captured_after_first=False,opponent_first_capture_at_s=None,captures={'A':0,'B':0},hold_s={'A':0.,'B':0.},control_at_s={},score_at_first=None,army_at_first=None)
    scores={str(k):v for k,v in initial.get('scores',{}).items()};alive={u['id']:(int(u['team']),u['type_id'] in world.vehicle_specs) for u in initial.get('units',[]) if u.get('alive',True)}
    checkpoints=(180,300,600,900);marks={id:0 for id in points};capture_order=[];team_first_capture={}
    def mark(until):
        for id,p in points.items():
            while marks[id]<len(checkpoints) and checkpoints[marks[id]]<until:
                t=checkpoints[marks[id]];p['control_at_s'][str(t)]=owners[id];marks[id]+=1
    for event in world.events:
        time=min(end,(event['sim_tick']+1)*tick_s);kind=event['event_kind'];payload=event['payload']
        if kind=='SCORE_TICK':scores={str(k):v for k,v in payload['scores'].items()}
        if kind=='UNIT_SPAWNED' and payload.get('entity'):
            u=payload['entity'];alive[u['id']]=(int(u['team']),u['type_id'] in world.vehicle_specs)
        if kind in ('INFANTRY_DISABLED','VEHICLE_DISABLED'):alive.pop(payload['unit'],None)
        id=str(payload.get('objective'))
        if id not in points or kind not in ('OBJECTIVE_CAPTURED','OBJECTIVE_NEUTRALIZED'):continue
        mark(time);p=points[id];before=owners[id]
        if before is not None:p['hold_s']['AB'[before]]+=time-last[id]
        after=int(payload['team']) if kind=='OBJECTIVE_CAPTURED' else None
        if p['first_team'] is not None and before==p['first_team'] and after!=before and not p['lost_after_first']:
            p['lost_after_first']=True;p['first_lost_at_s']=round(time,3)
        if kind=='OBJECTIVE_CAPTURED':
            p['captures']['AB'[after]]+=1
            team_first_capture.setdefault('AB'[after],dict(objective=id,team=after,at_s=round(time,3)))
            if p['first_team'] is not None and after!=p['first_team']:
                p['opponent_captured_after_first']=True
                if p['opponent_first_capture_at_s'] is None:p['opponent_first_capture_at_s']=round(time,3)
            if p['initial_owner'] is None and p['first_team'] is None:
                p['first_team']=after;p['first_at_s']=round(time,3);p['score_at_first']=dict(scores) if set(scores)>={'0','1'} else None
                p['army_at_first']={a:dict(infantry=sum(t==i and not v for t,v in alive.values()),vehicles=sum(t==i and v for t,v in alive.values())) for i,a in enumerate('AB')} if 'units' in initial else None
                capture_order.append(dict(objective=id,team=after,at_s=round(time,3),event_tick=event['sim_tick']))
            elif p['first_team']==after and p['lost_after_first']:p['regained_by_first']=True
        owners[id]=after;last[id]=time
    mark(end+1e-6)
    for id,p in points.items():
        if owners[id] is not None:p['hold_s']['AB'[owners[id]]]+=max(0,end-last[id])
        p['hold_s']={k:round(v,3) for k,v in p['hold_s'].items()};p['final_owner']=owners[id]
        if p['first_team'] is not None:p['first_stint_s']=round((p['first_lost_at_s'] if p['lost_after_first'] else end)-p['first_at_s'],3)
        for t in checkpoints:p['control_at_s'].setdefault(str(t),None if t<=end else 'not_reached')
    earliest=min((p['first_at_s'] for p in points.values() if p['first_at_s'] is not None),default=None)
    opening=[c for c in capture_order if c['at_s']==earliest]
    return dict(schema=1,available=True,duration_s=round(end,3),points=points,opening=opening,first_capture_order=capture_order,team_first_capture=team_first_capture)


def _add(target,source):
    for k,v in source.items():
        if isinstance(v,dict):_add(target.setdefault(k,{}),v)
        else:target[k]=target.get(k,0)+v
    return target


def _outcome(team,winner):return dict(n=1,wins=int(winner==team),losses=int(winner is not None and winner!=team),draws=int(winner is None))


def _contribution(row):
    result=dict(coverage=dict(matches=1,recorded=0,missing=1),points={},combinations={},opening={},team_first_capture={})
    profile=row.get('objective_stats')
    if not profile or profile.get('schema')!=1 or profile.get('available') is not True:return result
    result['coverage'].update(recorded=1,missing=0);winner=row['winner'];points=profile['points']
    for id,p in points.items():
        item=result['points'][id]=dict(matches=1,uncaptured=0,initially_owned=0,first={})
        if p['initial_owner'] is not None:item['initially_owned']=1;continue
        t=p['first_team']
        if t is None:item['uncaptured']=1;continue
        a='AB'[t];b='AB'[1-t];stats=_outcome(t,winner)
        stats.update(first_at_s_sum=p['first_at_s'],first_stint_s_sum=p['first_stint_s'],hold_s_sum=p['hold_s'][a],final_margin_sum=row['scores'][t]-row['scores'][1-t],lost_n=int(p['lost_after_first']),lost_wins=int(p['lost_after_first'] and winner==t),regained_n=int(p['regained_by_first']),regained_wins=int(p['regained_by_first'] and winner==t))
        score=p.get('score_at_first');army=p.get('army_at_first')
        if score is not None:stats.update(score_context_n=1,score_margin_at_first_sum=score[str(t)]-score[str(1-t)])
        if army is not None:stats.update(army_context_n=1,infantry_margin_at_first_sum=army[a]['infantry']-army[b]['infantry'],vehicle_margin_at_first_sum=army[a]['vehicles']-army[b]['vehicles'])
        stats.update(opponent_retake_n=int(p.get('opponent_captured_after_first',False)),opponent_retake_wins=int(p.get('opponent_captured_after_first',False) and winner==t))
        item['first'][a]=stats
    ids=sorted(points)
    for length in (2,3):
        for combo in combinations(ids,length):
            teams=[points[id]['first_team'] for id in combo]
            if teams[0] is not None and len(set(teams))==1:result['combinations']['+'.join(combo)]={'AB'[teams[0]]:_outcome(teams[0],winner)}
    for a,c in profile.get('team_first_capture',{}).items():result['team_first_capture'].setdefault(c['objective'],{})[a]=_outcome(c['team'],winner)
    opening=profile.get('opening',[])
    if len(opening)==1:
        c=opening[0];result['opening'][c['objective']]={'AB'[c['team']]:_outcome(c['team'],winner)}
    elif opening:result['opening']['simultaneous']={'n':1}
    return result


def document(rows):
    groups={};facets={key:set() for key in FILTERS};names=dict(NAMES)
    for r in rows:
        if r.get('kind')!='match' or r.get('ended') is not True:continue
        for id in (r.get('objective_stats') or {}).get('points',{}):names.setdefault(id,'거점 '+id)
        values={key:str(r.get(key) if r.get(key) is not None else 'unknown') for key in FILTERS}
        values['swapped']='true' if r.get('swapped') is True else 'false' if r.get('swapped') is False else 'unknown'
        values.update(policy_a=r['policies']['A'],policy_b=r['policies']['B'])
        for k,v in values.items():facets[k].add(v)
        key=tuple(values[k] for k in FILTERS)
        group=groups.setdefault(key,dict(conditions=values,summary={}))
        _add(group['summary'],_contribution(r))
    return dict(schema=1,objective_names=names,facets={k:sorted(v) for k,v in facets.items()},cohorts=list(groups.values()),note='상관관계 통계입니다. 최초 점령이 승리의 원인임을 증명하지 않습니다. 과거 누락 정보는 추정하지 않습니다.')


def report(doc,filters=None):
    filters=filters or {}
    if any(k not in FILTERS for k in filters):raise ValueError('unknown filter')
    result={}
    for group in doc['cohorts']:
        if all(group['conditions'].get(k)==v for k,v in filters.items() if v):_add(result,group['summary'])
    return dict(schema=1,filters=filters,facets=doc['facets'],objective_names=doc['objective_names'],note=doc['note'],**result)
