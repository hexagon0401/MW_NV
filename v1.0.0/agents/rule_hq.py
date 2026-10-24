"""Cheap deterministic decisions; no engine or world references."""
from math import hypot
from functools import lru_cache
from engine.catalog import load_vehicles

_vehicle_specs=lru_cache(maxsize=1)(load_vehicles)


class RuleHQ:
    def observe_and_issue(self,obs):
        commands=[];team=obs['team'];tick=obs['tick']
        units={u['id']:u for u in obs['units'] if u['alive']}
        reserved=set()
        objectives=sorted((f for f in obs['facilities'] if f['kind']=='OBJECTIVE'),key=lambda f:f['id'])
        depots=[f for f in obs['facilities'] if f['kind'] in ('HQ','SUPPLY_NODE') and f['owner']==team]
        for index,vehicle in enumerate(obs['vehicles']):
            if vehicle['fuel']>=20 or not depots or obs['resources']['supply']<30:continue
            target=min(depots,key=lambda f:hypot(f['pos']['x_cm']-vehicle['pos']['x_cm'],f['pos']['y_cm']-vehicle['pos']['y_cm']))
            distance=hypot(target['pos']['x_cm']-vehicle['pos']['x_cm'],target['pos']['y_cm']-vehicle['pos']['y_cm'])
            c=dict(v=1,cmd_id=tick*100+80+index,team=team,tick=tick,unit=vehicle['id'],ttl=750)
            if distance<=300:c.update(op=8,target=target['id'])
            else:c.update(op=7,arg0=target['pos']['x_cm']//100,arg1=target['pos']['y_cm']//100)
            commands.append(c)
            if len(commands)==4:return commands
        for index,group in enumerate(sorted(obs['squads'],key=lambda s:s['id'])):
            members=[units[i] for i in group['member_ids'] if i in units]
            if not members:continue
            onboard=[u for u in members if u['carrier_id'] is not None]
            if onboard:
                vehicle=next((v for v in obs['vehicles'] if v['id']==onboard[0]['carrier_id']),None)
                if vehicle is None or vehicle['task_state'] in ('WAITING_PASSENGERS','UNLOADING'):continue
                target=objectives[index%len(objectives)] if objectives else None
                if target is None:continue
                vp=vehicle['pos'];tp=target['pos']
                c=dict(v=1,cmd_id=tick*100+index+1,team=team,tick=tick,unit=vehicle['id'],ttl=750)
                if hypot(vp['x_cm']-tp['x_cm'],vp['y_cm']-tp['y_cm'])<target['radius_cm']:
                    c.update(op=6,arg0=vp['x_cm']//100,arg1=vp['y_cm']//100)
                else:c.update(op=7,arg0=tp['x_cm']//100,arg1=tp['y_cm']//100)
                commands.append(c)
                if len(commands)==4:break
                continue
            pos=members[0]['pos']
            def distance(f):return hypot(f['pos']['x_cm']-pos['x_cm'],f['pos']['y_cm']-pos['y_cm'])
            c=dict(v=1,cmd_id=tick*100+index+1,team=team,tick=tick,unit=group['id'],ttl=750)
            if any(u['type_id'] in ('INF','REC','SUP') and u['ammo']<3 for u in members) and depots and obs['resources']['supply']>=6*len(members):
                target=min(depots,key=distance)
                if all(hypot(u['pos']['x_cm']-target['pos']['x_cm'],u['pos']['y_cm']-target['pos']['y_cm'])<=300 for u in members):
                    c.update(op=8,target=target['id'])
                else:c.update(op=2,arg0=target['pos']['x_cm']//100,arg1=target['pos']['y_cm']//100)
            elif objectives:
                target=objectives[index%len(objectives)]
                alternatives=[f for f in objectives if f['owner']!=team]
                if target['owner']==team and alternatives:target=min(alternatives,key=distance)
                if distance(target)<=target['radius_cm']:
                    c.update(op=4 if target['owner']==team else 3,target=target['id'])
                else:c.update(op=2,arg0=target['pos']['x_cm']//100,arg1=target['pos']['y_cm']//100)
            else:c.update(op=1)
            # Use nearby idle carriers only when a complete squad fits.
            specs=_vehicle_specs()
            carriers=[v for v in obs['vehicles'] if v['id'] not in reserved and v['type_id'] in ('APC','HEL') and not v['passenger_ids'] and v['task_state'] in ('IDLE','READY','ARRIVED') and specs[v['type_id']]['capacity']>=len(members) and hypot(v['pos']['x_cm']-pos['x_cm'],v['pos']['y_cm']-pos['y_cm'])<10000]
            if c['op']==2 and carriers:
                carrier=min(carriers,key=lambda v:v['id']);reserved.add(carrier['id']);c.update(op=5,target=carrier['id'])
            commands.append(c)
            if len(commands)==4:break
        return commands
