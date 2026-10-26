"""Versioned event sequences with explicit missing evidence and censored windows."""
from math import hypot


def detect(world,commands,initial):
    if not initial:return dict(version='tactical-sequences-1',available=False,reason='missing initial frame')
    events=world.events;duration=300;end=world.tick;units=world.soldiers;facilities=world.facilities
    ownership={f['id']:[(initial['tick'],f.get('owner'))] for f in initial.get('facilities',[]) if f['kind']=='OBJECTIVE'}
    captures=[];disabled={};activity={};unloads=[];repairs=[];artillery=[]
    for e in events:
        p=e['payload'];t=e['sim_tick']+1;k=e['event_kind']
        if k in ('OBJECTIVE_CAPTURED','OBJECTIVE_NEUTRALIZED'):
            ownership.setdefault(p['objective'],[]).append((t,p.get('team') if k=='OBJECTIVE_CAPTURED' else None))
            if k=='OBJECTIVE_CAPTURED':captures.append((t,p))
        if k=='DISEMBARK_DONE':unloads.append((t,p))
        if k=='UNIT_REPAIRED':repairs.append((t,p))
        if k=='ARTILLERY_FIRED':artillery.append((t,p))
        if k=='VEHICLE_DISABLED':disabled[p['unit']]=t
        if k in ('UNIT_MOVED','ABSTRACT_ATTACK','EMBARK_DONE','DISEMBARK_DONE'):activity.setdefault(p.get('vehicle',p.get('unit')),[]).append(t)
    result={name:dict(opportunities=0,success=0,failed=0,censored=0,unknown=0,examples=[]) for name in ('unload_capture','artillery_capture','defend_hold','repair_operate')}
    def add(name,t,success,reference,known=True,definitive=False):
        r=result[name];r['opportunities']+=1;status='unknown' if not known else 'success' if success else 'failed' if definitive else 'censored' if end<t+duration else 'failed';r[status]+=1
        if len(r['examples'])<6:r['examples'].append(dict(tick=t,status=status,reference=reference))
    # One unload opportunity per squad/unload tick, not one per passenger.
    seen=set()
    for t,p in unloads:
        soldier=units.get(p['unit']);squad=getattr(soldier,'squad_id',None)
        if squad is None:continue
        key=(squad,t)
        if key in seen:continue
        seen.add(key);known=all('participants' in c for ct,c in captures if t<=ct<=t+duration)
        success=any(t<=ct<=t+duration and c['team']==int(soldier.team) and any(getattr(units.get(uid),'squad_id',None)==squad for uid in c.get('participants',[])) for ct,c in captures)
        add('unload_capture',t,success,dict(squad=squad,vehicle=p.get('vehicle')),known)
    for t,p in artillery:
        possible=[f for f in facilities.values() if f.kind=='OBJECTIVE' and hypot(f.pos.x_cm-p['x_cm'],f.pos.y_cm-p['y_cm'])<=f.radius_cm+1200]
        if not possible:continue
        add('artillery_capture',t,any(t<=ct<=t+duration and c['team']==p['team'] and c['objective'] in [f.id for f in possible] for ct,c in captures),dict(unit=p['unit'],objectives=[f.id for f in possible]))
    for team,rows in commands.items():
        for c in rows:
            if c['op']!=4:continue
            t=c['tick'];history=ownership.get(c['target'],[]);before=[owner for at,owner in history if at<=t]
            if not before or before[-1]!=('A','B').index(team):continue
            lost=any(t<at<=t+duration and owner!=('A','B').index(team) for at,owner in history)
            add('defend_hold',t,not lost and end>=t+duration,dict(unit=c['unit'],objective=c['target']),definitive=lost)
    seen=set()
    for t,p in repairs:
        uid=p['unit'];key=(uid,t//duration)
        if key in seen:continue
        seen.add(key);alive=disabled.get(uid,end+1)>t+duration;operated=any(t<at<=t+duration for at in activity.get(uid,[]))
        add('repair_operate',t,alive and operated and end>=t+duration,dict(unit=uid),definitive=disabled.get(uid,end+1)<=min(end,t+duration))
    return dict(version='tactical-sequences-1',window_seconds=60,available=True,patterns=result,causal_claim=False)
