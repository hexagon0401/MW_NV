"""tactics-4: scenario-normalized context64 plus64 semantic candidate rows24."""
import numpy as np
from engine.scenario_spec import specification

CONTRACT='tactics-4'
OBS_SIZE=1600
ACTIONS=65

def vector(obs,items):
    mission=obs.get('mission',{});config=mission.get('limits') or specification('2');catalog=obs['catalog'];own=[u for u in obs['units'] if u['alive']];vehicles=[v for v in obs['vehicles'] if v['alive'] and v['type_id']!='AA_SITE'];inf_cap=config['infantry_limit'];veh_cap=config['vehicle_limit'];mode=mission.get('mode','conquest');x=np.zeros(1600,dtype=np.float32)
    x[:11]=[len(own)/inf_cap,len(vehicles)/veh_cap,obs['resources']['credits']/max(1,config['credits']),obs['resources']['supply']/max(1,config['supply']*5),obs['resources']['tickets']/max(1,config['tickets']),obs['tick']*.2/config['time_limit_s'],obs['map_width_m']/4096,obs['map_height_m']/4096,float(mode=='conquest'),float(mode=='elimination'),float(mode=='capture_flag')]
    x[11:18]=[sum(u['hp']/catalog['units'][u['type_id']]['hp'] for u in own)/max(1,len(own)),sum(u['ammo']/max(1,catalog['units'][u['type_id']]['ammo']) for u in own)/max(1,len(own)),sum(catalog['vehicles'][v['type_id']].get('aircraft',v['type_id']=='HEL') for v in vehicles)/veh_cap,len(obs['enemies'])/(inf_cap+veh_cap),len(items)/64,0,0]
    for i,kind in enumerate(('INF','SUP','AT','REC','MED','ENG')):x[18+i]=sum(u['type_id']==kind for u in own)/inf_cap
    objectives=[f for f in obs['facilities'] if f['kind']=='OBJECTIVE']
    for i,owner in enumerate((obs['team'],1-obs['team'],None)):x[24+i]=sum(f['owner']==owner for f in objectives)/max(1,len(objectives))
    x[27:29]=[obs['scores'][obs['team']]/config.get('score_limit',1),obs['scores'][1-obs['team']]/config.get('score_limit',1)]
    for flag in mission.get('flags',[]):
        offset=29 if flag['owner']==obs['team'] else 35;x[offset:offset+5]=[float(flag['status']=='home'),float(flag['status']=='carried'),float(flag['status']=='dropped'),float(flag['position_known']),float(flag.get('carrier') in {u['id'] for u in own})]
    sites=mission.get('emplacements',[]);x[41:45]=[sum(s['observed'] for s in sites)/max(1,len(sites)),sum(s['owner_known'] and s['owner']==obs['team'] for s in sites)/max(1,len(sites)),sum(s['owner_known'] and s['owner'] is None for s in sites)/max(1,len(sites)),sum(v.get('air_only',False) for v in catalog['vehicles'].values())/max(1,len(catalog['vehicles']))]
    tickets=mission.get('own_combat_tickets')
    if tickets:x[45]=tickets['remaining']/max(1,tickets['initial'])
    x[46]=min(1,obs['scores'][obs['team']]/max(1,config.get('score_limit',1)))
    x[47]=float(bool(tickets))
    # tactics-4 was trained with empty history; do not inject evaluation-only state.
    diagonal=max(1,(obs['map_width_m']**2+obs['map_height_m']**2)**.5)
    all_own={u['id']:u for u in [*own,*vehicles]}
    for c in items:
        row=np.zeros(24,dtype=np.float32);row[:16]=c['features'][:16];actor=all_own.get(c['command']['unit']);spec=(catalog['units'] if actor and actor['type_id'] in catalog['units'] else catalog['vehicles']).get(actor['type_id'],{}) if actor else {}
        if c['command']['op']==11:
            from engine.economy import PURCHASE_TYPES
            kind=PURCHASE_TYPES[c['command']['arg0']];spec=(catalog['units'] if kind in catalog['units'] else catalog['vehicles'])[kind]
            row[3:6]=[spec['hp']/1000,spec['ammo']/240,spec['speed_mps']/14];row[7:14]=[spec['cost']/max(1,config['credits']),float(spec.get('aircraft',kind=='HEL')),float(spec['attack'] is not None),{'soft':0,'light':.33,'medium':.66,'heavy':1,'air':.25}[spec['armor']],float(kind in catalog['units']),spec.get('capacity',0)/16,float(c.get('tickets',0))]
        analysis=c.get('analysis',{});row[16:24]=[(spec.get('attack') or {}).get('range_m',0)/diagonal,analysis.get('distance_m',0)/diagonal,analysis.get('eta_s',0)/config['time_limit_s'],spec.get('capacity',0)/16,float(spec.get('air_only',False))+.5*float(spec.get('aircraft',actor is not None and actor['type_id']=='HEL')),c['command']['op']/21,1.,float(c['role'] in ('flag','return','recover','infiltrate'))];x[64+c['id']*24:64+(c['id']+1)*24]=row
    return np.clip(x,-4,4)
