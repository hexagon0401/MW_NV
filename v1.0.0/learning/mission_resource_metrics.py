"""Authoritative ammo intervals; missing old events never become guessed values."""
from collections import defaultdict


def collect(w,initial):
    if not initial:return dict(available=False,reason='missing initial state')
    state={u['id']:dict(team=u['team'],ammo=u.get('ammo'),tick=initial['tick'],alive=u['alive']) for u in initial['units'] if u.get('max_ammo',0)>0}
    totals=defaultdict(float);unknown=set();resupplied=defaultdict(int)
    for event in w.events:
        p=event['payload'];uid=p.get('unit');kind=event['event_kind'];tick=event['sim_tick']+1
        if uid not in state:
            u=w.soldiers.get(uid) or w.vehicles.get(uid)
            if not u or kind not in ('ABSTRACT_ATTACK','ARTILLERY_FIRED','UNIT_RESUPPLIED'):continue
            state[uid]=dict(team=int(u.team) if u.team is not None else None,ammo=None,tick=tick,alive=True);unknown.add(uid)
        row=state[uid]
        if kind not in ('ABSTRACT_ATTACK','ARTILLERY_FIRED','UNIT_RESUPPLIED','INFANTRY_DISABLED','VEHICLE_DISABLED'):continue
        if row['alive'] and row['ammo']==0:totals[row['team']]+=max(0,tick-row['tick'])*.2
        row['tick']=tick
        if kind.endswith('_DISABLED'):row['alive']=False
        elif 'ammo' in p:
            old=row['ammo'];row['ammo']=p['ammo']
            if kind=='UNIT_RESUPPLIED' and old is not None:resupplied[row['team']]+=max(0,p['ammo']-old)
        else:row['ammo']=None;unknown.add(uid)
    for row in state.values():
        if row['alive'] and row['ammo']==0:totals[row['team']]+=max(0,w.tick-row['tick'])*.2
    return dict(available=True,coverage='observed_intervals_only' if unknown else 'complete',unknown_units=len(unknown),zero_ammo_unit_seconds={str(t):v for t,v in totals.items() if t is not None},resupplied_rounds={str(t):v for t,v in resupplied.items() if t is not None})
