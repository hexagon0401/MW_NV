"""tactics-5: context64 plus64 rows32, shared training/teacher/evaluation encoder."""
import numpy as np
from math import hypot
from .mission_features import vector as base
CONTRACT='tactics-5'
OBS_SIZE=2112
ACTIONS=65


def vector(obs,items):
    old=base(obs,items);x=np.zeros(OBS_SIZE,np.float32);x[:64]=old[:64]
    history=obs.get('recent_summary',[])[:14];x[48:48+len(history)]=history
    diagonal=max(1,hypot(obs['map_width_m'],obs['map_height_m']))
    own={u['id']:u for u in obs['units']+obs['vehicles']}
    for s in obs['squads']:
        u=next((own[i] for i in s['member_ids'] if i in own and own[i]['alive']),None)
        if u:own[s['id']]=u
    for c in items:
        index=c['id'];row=x[64+index*32:64+(index+1)*32];row[:24]=old[64+index*24:64+(index+1)*24]
        a=own.get(c['command']['unit']);p=a['pos'] if a else dict(x_cm=0,y_cm=0);analysis=c.get('analysis',{});goal=analysis.get('route_goal',(c['command'].get('arg0',0)*100,c['command'].get('arg1',0)*100) if c['command']['op'] in (2,7,10) else (p['x_cm'],p['y_cm']))
        dx,dy=(goal[0]-p['x_cm'])/100,(goal[1]-p['y_cm'])/100
        hq=next((f for f in obs['facilities'] if f['kind']=='HQ' and f['owner']==obs['team']),None)
        if hq and hq['pos']['x_cm']>obs['map_width_m']*50:dx=-dx
        spec=obs['catalog']['vehicles'].get((a or {}).get('type_id'),{})
        fuel_margin=((a or {}).get('fuel',0)-analysis.get('path_length_m',analysis.get('distance_m',0))*spec.get('fuel_per_100m',0)/100)/max(1,spec.get('fuel_max',100))
        row[24:]=[dx/diagonal,dy/diagonal,analysis.get('path_length_m',analysis.get('distance_m',0))/diagonal,analysis.get('risk',0),analysis.get('cover',0),-1 if analysis.get('unexplored') is None else analysis.get('unexplored',-1),fuel_margin,analysis.get('eta_s',0)/max(1,obs.get('mission',{}).get('limits',{}).get('time_limit_s',3600))]
    return np.clip(x,-4,4)
