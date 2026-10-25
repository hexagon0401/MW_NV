"""Stateless team-anonymous NIM requests. API keys never enter prompt data."""
import json,random,itertools
from .tactics import compatible

def canonical_offer(obs,items):
    hq=next((f for f in obs['facilities'] if f['kind']=='HQ' and f['owner']==obs['team']),None)
    mirror=hq is not None and hq['pos']['x_cm']>obs['map_width_m']*50
    def position(pos):
        x=pos['x_cm']/(obs['map_width_m']*100);y=pos['y_cm']/(obs['map_height_m']*100)
        return [round(1-x if mirror else x,4),round(y,4)]
    entities={u['id']:u for u in [*obs['units'],*obs['vehicles'],*obs['squads'],*obs['facilities'],*obs['enemies']]}
    actors={u:i for i,u in enumerate(sorted({c['command']['unit'] for c in items}))}
    offered=list(items);random.Random(obs['tick']^0x51DE).shuffle(offered)
    locks={lock:i for i,lock in enumerate(sorted({lock for c in items for lock in c.get('locks',[])}))}
    output=[]
    for i,c in enumerate(offered):
        cmd=c['command'];actor=entities.get(cmd['unit']);target=entities.get(cmd['target'])
        goal=target['pos'] if target else dict(x_cm=cmd['arg0']*100,y_cm=cmd['arg1']*100) if cmd['op'] in (2,7,14) else None
        output.append(dict(id=i,actor='U'+str(actors[cmd['unit']]),role=c['role'],score=c['score'],op=cmd['op'],position=position(actor['pos']) if actor else None,goal=position(goal) if goal else None,locks=['L'+str(locks[k]) for k in c.get('locks',[])],cost=dict(credits=c.get('credits',0),tickets=c.get('tickets',0),supply=c.get('supply_cost',0)),condition=dict(health=c['features'][3],ammo=c['features'][4],fuel=c['features'][5]),analysis=c.get('analysis',{})))
    plans=[]
    for size in range(1,5):
        for ids in itertools.combinations(range(len(offered)),size):
            selected=[]
            for i in ids:
                if not compatible([offered[i]],selected):break
                selected.append(offered[i])
            else:plans.append((sum(c['score'] for c in selected),list(ids)))
    plans=[ids for _,ids in sorted(plans,key=lambda p:(-p[0],p[1]))[:12]] or [[]]
    compact=dict(valid_plans=plans,tick=obs['tick'],scores={'SELF':obs['scores'][obs['team']],'OPPONENT':obs['scores'][1-obs['team']]},resources=obs['resources'],candidates=output)
    return compact,{i:c for i,c in enumerate(offered)}

def choose(hq,obs,items):
    compact,lookup=canonical_offer(obs,items)
    payload=dict(model=hq.model,messages=[dict(role='system',content='Select a plan for SELF. Copy exactly one array from valid_plans into candidate_ids. Do not mix plans. Repeated actor IDs or shared locks conflict. Total costs must fit SELF resources. Return only JSON {"candidate_ids":[integers]}. No invented IDs. /no_think'),dict(role='user',content=json.dumps(compact,separators=(',',':')))],temperature=0,max_tokens=256,response_format={'type':'json_object'})
    result=json.loads(hq.transport(payload))
    if not isinstance(result,dict) or set(result)!={'candidate_ids'} or not isinstance(result['candidate_ids'],list) or len(result['candidate_ids'])>4:raise ValueError('teacher envelope')
    selected=[]
    for cid in result['candidate_ids']:
        if type(cid)is not int or cid not in lookup or not compatible([lookup[cid]],selected):raise ValueError('teacher invalid/conflicting ID')
        selected.append(lookup[cid])
    return selected
