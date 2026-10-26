"""Bounded mission candidates from permitted observations, never global enemy state."""
from collections import defaultdict,Counter
from math import hypot
from .tactics import candidates as legacy_candidates,compatible,BUSY
from engine.economy import PURCHASE_TYPES


def candidates(obs):
    mission=obs.get('mission',{});mode=mission.get('mode','conquest');catalog=obs['catalog'];own=[u for u in obs['units'] if u['alive'] and u['carrier_id'] is None];by_id={u['id']:u for u in own};vehicles=[v for v in obs['vehicles'] if v['alive']];facilities=obs['facilities'];hq=next(f for f in facilities if f['kind']=='HQ' and f['owner']==obs['team']);mirror=hq['pos']['x_cm']>obs['map_width_m']*50
    items=[c for c in legacy_candidates(obs) if not (mode!='conquest' and c['command']['op']==11) and not (c['command']['unit'] in {v['id'] for v in vehicles if catalog['vehicles'][v['type_id']].get('immobile')} and c['command']['op'] not in (8,13,17))]
    def add(actor,role,op,goal,score=90,target=0,reason='',locks=()):
        members=[by_id[i] for i in actor.get('member_ids',[]) if i in by_id];representative=members[0] if members else actor;kind=representative.get('type_id','INF');spec=(catalog['units'] if kind in catalog['units'] else catalog['vehicles'])[kind];x,y=goal['x_cm']//100,goal['y_cm']//100;p=representative['pos'];distance=hypot(p['x_cm']-goal['x_cm'],p['y_cm']-goal['y_cm'])/100
        command=dict(op=op,unit=actor['id'],target=target,arg0=x if op in (2,6,7,10,14) else 0,arg1=y if op in (2,6,7,10,14) else 0)
        if score<120 and any(o['unit']==actor['id'] and o['status'] in ('QUEUED','RUNNING') for o in obs.get('orders',[])):return
        if any(g['unit']==actor['id'] and hypot(g['x_cm']-goal['x_cm'],g['y_cm']-goal['y_cm'])<400 for g in obs.get('failed_goals',[])):return
        if any(o['unit']==actor['id'] and all(o.get(k)==command[k] for k in ('op','target','arg0','arg1')) and o['status'] in ('QUEUED','RUNNING') for o in obs.get('orders',[])):return
        hp=sum(u['hp']/catalog['units'][u['type_id']]['hp'] for u in members)/len(members) if members else representative.get('hp',spec['hp'])/spec['hp']
        features=[score/200,1-p['x_cm']/(obs['map_width_m']*100) if mirror else p['x_cm']/(obs['map_width_m']*100),p['y_cm']/(obs['map_height_m']*100),hp,representative.get('ammo',0)/max(1,spec['ammo']),representative.get('fuel',100)/100,0,len(members)/8,float(kind in catalog['vehicles']),float(role=='fire'),float(role=='anti_armor'),float(role=='transport'),float(role=='supply'),float(role=='retreat'),1-goal['x_cm']/(obs['map_width_m']*100) if mirror else goal['x_cm']/(obs['map_width_m']*100),goal['y_cm']/(obs['map_height_m']*100)]
        candidate=dict(role=role,score=score,reason=reason,command=command,features=features,locks=sorted(set([actor['id'],*actor.get('member_ids',[]),*locks])),supply_cost=0,supply_budget=obs['resources']['supply'],credits=0,tickets=0,credit_budget=obs['resources']['credits'],ticket_budget=obs['resources']['tickets'],analysis=dict(tactic=role,distance_m=distance,eta_s=distance/max(.1,spec['speed_mps'])))
        items.append(candidate);return candidate
    carrier_ids={f['carrier'] for f in mission.get('flags',[]) if f['status']=='carried' and f.get('carrier') is not None}
    squads=[s for s in obs['squads'] if not carrier_ids.intersection(s['member_ids']) and any(i in by_id for i in s['member_ids']) and all(i in by_id for i in s['member_ids'] if any(u['id']==i and u['alive'] for u in obs['units']))]
    goals=[]
    if mode=='elimination':
        goals=[e['pos'] for e in obs['enemies']]+[dict(x_cm=e['x_cm'],y_cm=e['y_cm']) for e in obs.get('last_seen',[]) if obs['tick']-e['seen_at_tick']<=50]
        if not goals:goals=[dict(x_cm=round(obs['map_width_m']*100*f),y_cm=round(obs['map_height_m']*100*g)) for f,g in ((.5,.25),(.5,.5),(.5,.75),(.75 if not mirror else .25,.5))]
        for squad in squads:
            for goal in goals[:4]:add(squad,'recon' if not obs['enemies'] else 'attack',2,goal,85,reason='전투 지역 정찰' if not obs['enemies'] else '관측 전투 구역 접근')
    if mode=='capture_flag':
        enemy_hq=next(f for f in facilities if f['kind']=='HQ' and f['owner']!=obs['team']);own_flag=next(f for f in mission['flags'] if f['owner']==obs['team']);enemy_flag=next(f for f in mission['flags'] if f['owner']!=obs['team'])
        goals=[enemy_hq['pos']]
        for squad in squads:
            base=mission['bases'].get(1-obs['team'],mission['bases'].get(str(1-obs['team'])))
            room=base['room'];inside_members=[by_id[i] for i in squad['member_ids'] if i in by_id and room[0]<=by_id[i]['pos']['x_cm']<room[2] and room[1]<=by_id[i]['pos']['y_cm']<room[3]]
            if len(inside_members)>=3 and enemy_flag['status']=='home':add(squad,'flag',19,enemy_hq['pos'],155,target=enemy_hq['id'],reason='깃발실 확보·탈취 상호작용 유지')
            add(squad,'infiltrate',18,enemy_hq['pos'],95,target=enemy_hq['id'],reason='출입구를 통해 적 깃발실 진입')
            add(squad,'defend',18,hq['pos'],80,target=hq['id'],reason='아군 깃발실 방어')
            for flag in (own_flag,enemy_flag):
                if flag['status']=='dropped' and flag['position_known']:
                    near=any(hypot(by_id[i]['pos']['x_cm']-flag['pos']['x_cm'],by_id[i]['pos']['y_cm']-flag['pos']['y_cm'])<=400 for i in squad['member_ids'] if i in by_id)
                    add(squad,'recover' if flag['owner']==obs['team'] else 'flag',19 if near else 2,flag['pos'],130,target=(hq if flag['owner']==obs['team'] else enemy_hq)['id'] if near else 0,reason='관측된 깃발 회수' if near else '관측된 깃발 회수 접근')
                elif flag['status']=='carried' and flag['position_known'] and flag['carrier'] not in {u['id'] for u in obs['units']}:add(squad,'intercept',2,flag['pos'],115,reason='관측된 운반자 차단')
        carrier=by_id.get(enemy_flag.get('carrier'))
        if carrier:
            base=mission['bases'].get(obs['team'],mission['bases'].get(str(obs['team'])));zone=base['return_zone']
            if zone[0]<=carrier['pos']['x_cm']<zone[2] and zone[1]<=carrier['pos']['y_cm']<zone[3]:add(carrier,'return',19,hq['pos'],175,target=enemy_hq['id'],reason='아군 본진·깃발 반납 유지')
            add(carrier,'return',2,hq['pos'],160,reason='탈취한 깃발을 본진으로 귀환')
            for v in vehicles:
                if v['task_state'] not in BUSY+('HOVERING',) and catalog['vehicles'][v['type_id']]['capacity']-len(v['passenger_ids'])>=1 and hypot(v['pos']['x_cm']-carrier['pos']['x_cm'],v['pos']['y_cm']-carrier['pos']['y_cm'])<=10000:add(carrier,'transport',5,v['pos'],140,target=v['id'],reason='깃발 운반자 지상·항공 수송',locks=[v['id']])
        if enemy_flag.get('carrier') is not None:
            transport=next((v for v in vehicles if enemy_flag['carrier'] in v['passenger_ids']),None)
            if transport:
                from engine.traffic import arrival_slot
                slot=arrival_slot(obs,transport,hq['pos'])
                if hypot(transport['pos']['x_cm']-hq['pos']['x_cm'],transport['pos']['y_cm']-hq['pos']['y_cm'])<=10000:add(transport,'return',6,transport['pos'],175,reason='본진 도착·운반자 하차')
                elif slot:add(transport,'return',7,dict(x_cm=slot[0]*100,y_cm=slot[1]*100),165,reason='깃발 운반 차량 본진 귀환')
    if mode!='conquest':
        from engine.traffic import arrival_slot
        for squad in squads:
            members=[by_id[i] for i in squad['member_ids'] if i in by_id]
            for vehicle in vehicles:
                spec=catalog['vehicles'][vehicle['type_id']]
                if spec['capacity']>=len(members) and not vehicle['passenger_ids'] and vehicle['task_state'] not in BUSY and hypot(vehicle['pos']['x_cm']-members[0]['pos']['x_cm'],vehicle['pos']['y_cm']-members[0]['pos']['y_cm'])<10000:
                    add(squad,'transport',5,vehicle['pos'],105,target=vehicle['id'],reason='임무 지역으로 분대 수송',locks=[vehicle['id']]);break
        for vehicle in vehicles:
            spec=catalog['vehicles'][vehicle['type_id']]
            if carrier_ids.intersection(vehicle['passenger_ids']) or spec.get('immobile') or vehicle['task_state'] in BUSY or vehicle['fuel']<=0:continue
            for goal in goals[:3]:
                if vehicle['passenger_ids'] and hypot(vehicle['pos']['x_cm']-goal['x_cm'],vehicle['pos']['y_cm']-goal['y_cm'])<10000:
                    add(vehicle,'transport',6,vehicle['pos'],150,reason='임무 구역 도착·하차');continue
                if vehicle.get('deployment')!='PACKED':continue
                slot=arrival_slot(obs,vehicle,goal)
                if slot:add(vehicle,'transport' if vehicle['passenger_ids'] else 'anti_air' if spec.get('air_only') else 'fire' if vehicle['type_id']=='SPH' else 'attack',7,dict(x_cm=slot[0]*100,y_cm=slot[1]*100),95 if vehicle['passenger_ids'] else 70,reason='임무 지원 위치 확보')
        for vehicle in vehicles:
            if vehicle['type_id']=='AA_SITE' and not any(e['type_id'] in catalog['vehicles'] and catalog['vehicles'][e['type_id']].get('aircraft',e['type_id']=='HEL') for e in obs['enemies']):
                crew=next((u for u in obs['units'] if u['carrier_id']==vehicle['id']),None)
                if crew:add(crew,'recon',21,vehicle['pos'],35,target=vehicle['id'],reason='대공 진지 승무원 해제')
    for site in mission.get('emplacements',[]):
        if site.get('observed') and site.get('alive') and site.get('owner') is None and site.get('ammo',0)>0 and own:
            soldier=min(own,key=lambda u:(hypot(u['pos']['x_cm']-site['pos']['x_cm'],u['pos']['y_cm']-site['pos']['y_cm']),u['id']));distance=hypot(soldier['pos']['x_cm']-site['pos']['x_cm'],soldier['pos']['y_cm']-site['pos']['y_cm'])
            add(soldier,'anti_air',20 if distance<=400 else 2,site['pos'],110,target=site['id'] if distance<=400 else 0,reason='중립 대공 진지 운용',locks=[site['id']])
        elif squads and not site.get('observed'):add(min(squads,key=lambda s:s['id']),'recon',2,site['pos'],60,reason='중립 대공 진지 정찰')
    if mode!='conquest':
        desired=dict(mission.get('desired_roster',{}));initial_infantry=sum(v for k,v in desired.items() if k in catalog['units'])
        from math import ceil
        desired={k:ceil(v*mission['limits']['infantry_limit']/max(1,initial_infantry)) if k in catalog['units'] else v for k,v in desired.items()};desired.setdefault('AA',1);counts=Counter(u['type_id'] for u in obs['units'] if u['alive'])+Counter(v['type_id'] for v in vehicles)
        for kind,amount in desired.items():
            infantry=kind in catalog['units'];spec=(catalog['units'] if infantry else catalog['vehicles'])[kind];living=sum(counts[k] for k in (catalog['units'] if infantry else catalog['vehicles']) if k!='AA_SITE')
            if counts[kind]>=amount or living>=mission['limits']['infantry_limit' if infantry else 'vehicle_limit'] or obs['resources']['credits']<spec['cost'] or infantry and not obs['resources']['tickets']:continue
            c=add(hq,'supply',11,hq['pos'],100,target=hq['id'],reason='시나리오 편성 손실 보충')
            if c:c['command']['arg0']=PURCHASE_TYPES.index(kind);c.update(credits=spec['cost'],tickets=int(infantry))
    buckets=defaultdict(lambda:defaultdict(list));seen=set()
    for c in sorted(items,key=lambda c:(-c['score'],c['command']['unit'],tuple(c['command'].values()))):
        key=tuple(c['command'][k] for k in ('op','unit','target','arg0','arg1'))
        if key in seen:continue
        seen.add(key);buckets[c['role']][c['command']['unit']].append(c)
    queues={}
    for role,actors in buckets.items():
        queues[role]=[actors[actor][layer] for layer in range(max(map(len,actors.values()))) for actor in sorted(actors) if layer<len(actors[actor])]
    result=[]
    while len(result)<64 and any(queues.values()):
        for role in sorted(queues):
            if queues[role]:result.append(queues[role].pop(0))
            if len(result)==64:break
    for i,c in enumerate(result):c['id']=i
    return result


def commands(obs,selected):
    from .tactics import commands as legacy
    result=legacy(obs,selected)
    if obs.get('mission',{}).get('mode','conquest')!='conquest':
        for command,candidate in zip(result,selected):
            # Large mission maps need distance-aware TTL; engine still bounds physical movement.
            if command['op'] in (2,7,10,18):command['ttl']=max(command['ttl'],min(18000,round((candidate.get('analysis',{}).get('eta_s',0)*1.8+90)*5)))
    return result
