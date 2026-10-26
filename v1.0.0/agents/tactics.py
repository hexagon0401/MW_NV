"""Pure, bounded tactical candidates derived exclusively from team observations."""
from math import hypot,ceil,isfinite
from zipfile import BadZipFile
from collections import defaultdict

CONTRACT='tactics-2'
ROLES=('capture','defend','recon','anti_armor','fire','transport','supply','repair','retreat')
BUSY=('MOVING','TAKEOFF','LANDING','WAITING_PASSENGERS','UNLOADING','DEPLOYING','PACKING','WAITING_TRAFFIC')


def distance(a,b):return hypot(a['pos']['x_cm']-b['pos']['x_cm'],a['pos']['y_cm']-b['pos']['y_cm'])/100


def candidates(obs):
    catalog=obs['catalog'];own=[u for u in obs['units'] if u['alive']];vehicles=[v for v in obs['vehicles'] if v['alive']]
    own_by={u['id']:u for u in own};enemies=obs['enemies'];objectives=sorted((f for f in obs['facilities'] if f['kind']=='OBJECTIVE'),key=lambda f:f['id'])
    depots=[f for f in obs['facilities'] if f['owner']==obs['team'] and (f['kind']=='HQ' or f.get('supply_per_minute',0))]+[v for v in vehicles if v['type_id']=='TRK' and v['cargo_supply']>0]
    result=[]
    def clear(a,b):
        terrain=obs.get('terrain')
        if terrain is None:return True
        n=max(1,ceil(distance(a,b)))
        return all(terrain[round(a['pos']['y_cm']+(b['pos']['y_cm']-a['pos']['y_cm'])*i/n)//400][round(a['pos']['x_cm']+(b['pos']['x_cm']-a['pos']['x_cm'])*i/n)//400] not in (3,4) for i in range(n+1))

    def direct(actor,target,s):
        if actor.get('ammo',0)<=0 or not s['attack']:return False
        if actor['type_id']=='MBT' and any(distance(friend,target)<catalog['weapons']['tank_splash']['blast_m'] for friend in [*own,*vehicles] if friend.get('carrier_id') is None and not (friend['type_id']=='HEL' and friend['task_state'] in ('TAKEOFF','MOVING','LANDING'))):return False
        enemy_spec=(catalog['units'] if target['type_id'] in catalog['units'] else catalog['vehicles'])[target['type_id']]
        defense='light' if target['type_id']=='HEL' and target['task_state'] not in ('MOVING','TAKEOFF','LANDING') else enemy_spec['armor']
        if catalog['weapons']['multipliers'][s['weapon']][defense]<=0:return False
        detect=s['detection_m'];terrain=obs.get('terrain')
        if any((f['kind']=='TOWER' or f['kind']=='OBJECTIVE' and f['id']==201) and f['owner']==obs['team'] and distance(actor,f)<=f['radius_cm']/100 for f in obs['facilities']):detect*=1.2
        if terrain:
            if terrain[actor['pos']['y_cm']//400][actor['pos']['x_cm']//400]==2:detect*=.7
            if terrain[target['pos']['y_cm']//400][target['pos']['x_cm']//400]==2:detect*=.8
        return distance(actor,target)<=min(s['attack']['range_m'],detect) and clear(actor,target)
    def add(actor,role,score,reason,op,target=0,x=0,y=0,reservations=None,variant='direct'):
        members=actor.get('member_ids',[]);troops=[own_by[i] for i in members if i in own_by]
        representative=troops[0] if troops else actor
        pos=representative['pos'];kind=representative.get('type_id','INF');spec=(catalog['units'] if kind in catalog['units'] else catalog['vehicles'])[kind]
        threat=sum(max(0,1-distance(representative,e)/160) for e in enemies)
        health=sum(u['hp']/catalog['units'][u['type_id']]['hp'] for u in troops)/len(troops) if troops else representative.get('hp',spec['hp'])/spec['hp']
        ammo=representative.get('ammo',0)/max(1,spec.get('ammo',0))
        goal=next((u for u in [*enemies,*vehicles,*obs['facilities']] if u['id']==target),None)
        goal_pos=goal['pos'] if goal else dict(x_cm=x*100,y_cm=y*100)
        meters=hypot(pos['x_cm']-goal_pos['x_cm'],pos['y_cm']-goal_pos['y_cm'])/100 if target or x or y else 0
        if any(g['unit']==actor['id'] and hypot(g['x_cm']-goal_pos['x_cm'],g['y_cm']-goal_pos['y_cm'])<400 for g in obs.get('failed_goals',[])):return
        if any(o['unit']==actor['id'] and o['op']==op and o['target']==target and o['arg0']==x and o['arg1']==y and o['status'] in ('QUEUED','RUNNING') for o in obs.get('orders',[])):return
        analysis=dict(tactic=variant,distance_m=round(meters,1),eta_s=round(meters/max(.1,min(catalog['units'][u['type_id']]['speed_mps'] for u in troops) if troops else spec['speed_mps']),1),observed_threats=round(threat,2))
        if op==13 and goal and spec['attack']:
            enemy_spec=(catalog['units'] if goal['type_id'] in catalog['units'] else catalog['vehicles'])[goal['type_id']]
            defense='light' if goal['type_id']=='HEL' and goal['task_state'] not in ('MOVING','TAKEOFF','LANDING') else enemy_spec['armor']
            hit=spec['attack']['hit_probability'];terrain=obs.get('terrain')
            if terrain and terrain[goal_pos['y_cm']//400][goal_pos['x_cm']//400]==2:hit*=.8
            expected=spec['attack']['damage']*catalog['weapons']['multipliers'][spec['weapon']][defense]*hit
            analysis.update(expected_damage=round(expected,2),target_type=goal['type_id'],target_armor=defense,hit_probability=round(hit,3))
            score+=min(25,expected/max(1,goal['hp'])*20);reason+=f' · {goal["type_id"]} 예상 {expected:.1f}'
        hq=next((f for f in obs['facilities'] if f['kind']=='HQ' and f['owner']==obs['team']),None)
        mirrored=hq is not None and hq['pos']['x_cm']>obs['map_width_m']*50
        features=[score/200,(1-pos['x_cm']/(obs['map_width_m']*100)) if mirrored else pos['x_cm']/(obs['map_width_m']*100),pos['y_cm']/(obs['map_height_m']*100),health,ammo,representative.get('fuel',100)/100,min(1,threat/4),len(troops)/8,float(kind in catalog['vehicles']),float(role=='fire'),float(role=='anti_armor'),float(role=='transport'),float(role=='supply'),float(role=='retreat'),(1-goal_pos['x_cm']/(obs['map_width_m']*100)) if mirrored else goal_pos['x_cm']/(obs['map_width_m']*100),goal_pos['y_cm']/(obs['map_height_m']*100)]
        cost=0
        if op==17:cost=2
        elif op==9:cost=1
        elif op==8:
            if troops:
                cost=sum(2*ceil(max(0,catalog['units'][u['type_id']]['ammo']-u['ammo'])/10)+ceil(max(0,catalog['units'][u['type_id']]['heal_pool']-u['heal_pool'])/10)+ceil(max(0,catalog['units'][u['type_id']]['repair_pool']-u['repair_pool'])/10) for u in troops)
            elif kind in catalog['vehicles']:cost=ceil(max(0,spec['fuel_max']-representative['fuel'])/10)*3+ceil(max(0,spec['ammo']-representative['ammo'])/10)*2
        credits=0;tickets=0
        if op==11:
            from engine.economy import PURCHASE_TYPES
            purchased=PURCHASE_TYPES[x];infantry=purchased in catalog['units'];credits=(catalog['units'] if infantry else catalog['vehicles'])[purchased]['cost'];tickets=int(infantry)
        if credits>obs['resources']['credits'] or tickets>obs['resources']['tickets']:return
        if op==8:
            truck=next((v for v in vehicles if v['id']==target),None)
            if truck:
                if cost>truck['cargo_supply']:return
                reservations=[*(reservations or []),truck['id']];cost=0
        budget=obs['resources']['supply']
        if cost>budget:return
        result.append(dict(analysis=analysis,credits=credits,tickets=tickets,credit_budget=obs['resources']['credits'],ticket_budget=obs['resources']['tickets'],supply_cost=cost,supply_budget=budget,role=role,score=round(score,4),reason=reason,command=dict(op=op,unit=actor['id'],target=target,arg0=x,arg1=y),features=features,locks=sorted(set([actor['id'],*members,*(reservations or [])]))) )
    def goto(actor,role,target,score,reason,op=2):
        x=target['pos']['x_cm']//100;y=target['pos']['y_cm']//100
        troops=[own_by[i] for i in actor.get('member_ids',[]) if i in own_by]
        if role=='supply' and troops:
            x-=round((sum(t['pos']['x_cm'] for t in troops)/len(troops)-troops[0]['pos']['x_cm'])/100);y-=round((sum(t['pos']['y_cm'] for t in troops)/len(troops)-troops[0]['pos']['y_cm'])/100)
        add(actor,role,score,reason,op,x=x,y=y)
    for g in sorted(obs['squads'],key=lambda g:g['id']):
        troops=[own_by[i] for i in g['member_ids'] if i in own_by];dismounted=[u for u in troops if u['carrier_id'] is None]
        if not troops or not dismounted:continue
        if any(o.get('unit')==g['id'] and o.get('op')==5 and o['status'] in ('QUEUED','RUNNING') for o in obs.get('orders',[])):continue
        if len(dismounted)!=len(troops):continue
        actor=troops[0];hp=sum(u['hp']/catalog['units'][u['type_id']]['hp'] for u in troops)/len(troops)
        nearby=[e for e in enemies if distance(actor,e)<130]
        for f in objectives:
            d=distance(actor,f);role='defend' if f['owner']==obs['team'] else 'capture'
            score=70-d*.12+(15 if role=='capture' else 0)+min(20,len(troops)*2)
            if role=='defend' and not nearby:score-=30
            add(g,role,score,'거점 확보' if role=='capture' else '거점 방어',3 if role=='capture' else 4,target=f['id'])
            terrain=obs.get('terrain')
            if terrain:
                for side in (-1,1):
                    gx=f['pos']['x_cm']//100;gy=f['pos']['y_cm']//100+side*48
                    if 4<=gx<obs['map_width_m']-4 and 4<=gy<obs['map_height_m']-4 and terrain[gy//4][gx//4] in (0,1,2,5,7,8):
                        add(g,role,score-12,'거점 측면 경유',2,x=gx,y=gy,variant='flank_north' if side<0 else 'flank_south')
                cover=[]
                for cy in range(max(0,actor['pos']['y_cm']//400-10),min(len(terrain),actor['pos']['y_cm']//400+11)):
                    for cx in range(max(0,actor['pos']['x_cm']//400-10),min(len(terrain[0]),actor['pos']['x_cm']//400+11)):
                        if terrain[cy][cx]==2:cover.append((abs(cx*400-f['pos']['x_cm'])+abs(cy*400-f['pos']['y_cm']),cx,cy))
                if cover:
                    _,cx,cy=min(cover);add(g,'defend',score-8,'엄폐 위치 확보',2,x=cx*4+2,y=cy*4+2,variant='cover')

        if any(u['type_id']=='REC' for u in troops) and objectives:
            f=objectives[(g['id']+obs['tick']//150)%len(objectives)];goto(g,'recon',f,70-distance(actor,f)*.1,'거점 접근 정찰')
        if hp<.35 and depots:goto(g,'retreat',min(depots,key=lambda d:distance(actor,d)),115,'분대 체력 부족',10)
        low=any(catalog['units'][u['type_id']]['ammo'] and u['ammo']<max(1,catalog['units'][u['type_id']]['ammo']*.2) for u in troops)
        if low and depots:
            depot=min(depots,key=lambda d:distance(actor,d))
            if all(distance(u,depot)<=3 for u in troops):add(g,'supply',125,'탄약 부족·재보급',8,target=depot['id'])
            else:goto(g,'supply',depot,110-distance(actor,depot)*.1,'탄약 부족·보급 이동')
        if objectives:
            objective=min((f for f in objectives if f['owner']!=obs['team']),key=lambda f:distance(actor,f),default=objectives[0])
            if distance(actor,objective)>150:
                carriers=[v for v in vehicles if v['type_id'] in ('APC','IFV','HEL') and v['task_state'] not in BUSY and not v['passenger_ids'] and catalog['vehicles'][v['type_id']]['capacity']>=len(troops) and distance(actor,v)<100]
                if carriers:
                    v=min(carriers,key=lambda v:(distance(actor,v),v['id']));add(g,'transport',100-distance(actor,v)*.15,'완편 분대 수송',5,target=v['id'],reservations=[v['id']])
        for u in troops:
            us=catalog['units'][u['type_id']]
            if u['type_id']=='AT':
                targets=[e for e in enemies if e['type_id'] in catalog['vehicles'] and direct(u,e,us)]
                if targets:
                    e=min(targets,key=lambda e:(distance(u,e),e['id']));add(u,'anti_armor',130,'확인된 장갑 위협 대응',13,target=e['id'])
            if u['type_id']=='ENG' and u['repair_pool']>=10 and obs['resources']['supply']>=2:
                damaged=[v for v in vehicles if v['hp']<catalog['vehicles'][v['type_id']]['hp'] and v['task_state'] not in BUSY]
                if damaged:
                    v=min(damaged,key=lambda v:distance(u,v))
                    hull=catalog['vehicles'][v['type_id']]['footprint_cm'];dx=max(0,abs(u['pos']['x_cm']-v['pos']['x_cm'])-hull[0]/2);dy=max(0,abs(u['pos']['y_cm']-v['pos']['y_cm'])-hull[1]/2)
                    if hypot(dx,dy)<=300:add(u,'repair',120,'손상 차량 수리',17,target=v['id'],reservations=[v['id']])
                    else:goto(u,'repair',v,80-distance(u,v)*.1,'손상 차량 접근')
            if u['type_id']=='MED' and u['heal_pool']>=8:
                wounded=[s for s in troops if s['hp']<catalog['units'][s['type_id']]['hp'] and distance(u,s)<=3 and s['task_state']!='MOVING']
                if wounded:add(u,'repair',110,'부상병 치료',9,target=wounded[0]['id'],reservations=[wounded[0]['id']])
    for v in sorted(vehicles,key=lambda v:v['id']):
        vs=catalog['vehicles'][v['type_id']]
        if v['task_state'] in BUSY:continue
        if v['fuel']<20 or vs['ammo'] and v['ammo']<max(1,vs['ammo']*.2):
            if depots:
                depot=min((d for d in depots if d['id']!=v['id']),key=lambda d:distance(v,d),default=None)
                if depot:
                    if distance(v,depot)<=3:add(v,'supply',140,'차량 연료·탄약 보급',8,target=depot['id'])
                    elif v['deployment']=='PACKED' and v['fuel']>0:goto(v,'supply',depot,130,'차량 보급 이동',7)
                    elif v['deployment']!='PACKED':add(v,'supply',130,'보급 이동 전 철수',16)
            continue
        from engine.traffic import arrival_slot
        if v.get('needs_parking') and not v['passenger_ids']:
            slot=arrival_slot(obs,v,v['pos'],parking=True)
            if slot:add(v,'transport',150,'하차 후 통행로 확보·분산 주차',7,x=slot[0],y=slot[1])
            continue
        if v['passenger_ids']:
            target=min((f for f in objectives if f['owner']!=obs['team']),key=lambda f:distance(v,f),default=objectives[0] if objectives else None)
            if target:
                if distance(v,target)<=target['radius_cm']/100:add(v,'transport',145,'거점 도착·하차',6,x=v['pos']['x_cm']//100,y=v['pos']['y_cm']//100)
                else:
                    slot=arrival_slot(obs,v,target['pos'])
                    if slot:add(v,'transport',140,'분산 하차 지점 수송',7,x=slot[0],y=slot[1])
            continue
        if v['type_id']=='SPH':
            sightings={e['id']:dict(x_cm=e['pos']['x_cm'],y_cm=e['pos']['y_cm'],seen_at_tick=obs['tick']) for e in enemies}
            for s in obs.get('last_seen',[]):
                if 0<=obs['tick']-s['seen_at_tick']<=50:sightings.setdefault(s['id'],s)
            valid=[]
            for target in sightings.values():
                point=dict(pos=target);d=distance(v,point)
                if 100<=d<=420 and not any(distance(f,point)<20 for f in [*own,*vehicles]):valid.append(target)
            if valid and v['ammo']:
                if v['deployment']=='DEPLOYED':
                    for t in valid[:4]:add(v,'fire',135,'포격 가능·관측 유효·아군 없음',14,x=t['x_cm']//100,y=t['y_cm']//100)
                else:add(v,'fire',130,'관측 표적 대응·포병 설치',15)
            elif v['deployment']!='PACKED':add(v,'fire',75,'표적 없음·포병 철수',16)
            elif objectives:
                f=min(objectives,key=lambda f:distance(v,f));base=next((b for b in obs['facilities'] if b['kind']=='HQ' and b['owner']==obs['team']),v);x=f['pos']['x_cm']//100+(-220 if base['pos']['x_cm']<obs['map_width_m']*50 else 220)
                if abs(v['pos']['x_cm']//100-x)>30:add(v,'fire',65,'포병 사거리 확보',7,x=max(12,min(obs['map_width_m']-12,x)),y=f['pos']['y_cm']//100)
        elif vs['attack']:
            targets=[e for e in enemies if direct(v,e,vs)]
            if targets:
                e=min(targets,key=lambda e:(distance(v,e),e['id']));add(v,'anti_armor',125,'직사 화력 지원',13,target=e['id'])
            elif objectives:
                target=min(objectives,key=lambda f:distance(v,f));slot=arrival_slot(obs,v,target['pos'])
                if slot:add(v,'anti_armor',65,'분산 화력 배치',7,x=slot[0],y=slot[1])
    from engine.economy import PURCHASE_TYPES
    hq=next((f for f in obs['facilities'] if f['kind']=='HQ' and f['owner']==obs['team']),None)
    if hq:
        desired={'INF':30,'SUP':6,'AT':10,'REC':6,'MED':8,'ENG':4,'LUV':1,'APC':2,'IFV':2,'MBT':2,'SPH':1,'HEL':1,'TRK':1}
        for kind,amount in desired.items():
            living=own if kind in catalog['units'] else vehicles
            deficit=amount-sum(u['type_id']==kind for u in living)
            if deficit>0 and len(living)<(96 if kind in catalog['units'] else 14):add(hq,'supply',100+min(25,deficit*3),'손실 병종 우선 충원',11,target=hq['id'],x=PURCHASE_TYPES.index(kind))
    # Offer alternative disembark objectives instead of hard-wiring the nearest point.
    for v in sorted(vehicles,key=lambda v:v['id']):
        if not v['passenger_ids'] or v['task_state'] in ('TAKEOFF','LANDING','UNLOADING'):continue
        from engine.traffic import arrival_slot
        for f in objectives:
            slot=arrival_slot(obs,v,f['pos'])
            if slot:add(v,'transport',125-distance(v,f)*.03,'수송 목적지 선택',7,x=slot[0],y=slot[1],variant='transport_destination')
    # Fair role allocation keeps scarce support actions in the bounded candidate set.
    buckets=defaultdict(lambda:defaultdict(list))
    for item in sorted(result,key=lambda c:(-c['score'],c['command']['unit'],c['command']['op'],c['command']['target'],c['command']['arg0'],c['command']['arg1'])):buckets[item['role']][item['command']['unit']].append(item)
    chosen=[];seen=set();cycle=0
    while len(chosen)<64:
        added=False
        for role in ROLES:
            for uid in sorted(buckets[role]):
                items=buckets[role][uid]
                if cycle>=len(items):continue
                item=items[cycle];identity=tuple(item['command'].values())
                if identity in seen:continue
                seen.add(identity);chosen.append(item);added=True
                if len(chosen)==64:break
            if len(chosen)==64:break
        cycle+=1
        if not added:break
    for i,c in enumerate(chosen):c['id']=i
    return chosen


def compatible(items,selected):
    locks={uid for c in selected for uid in c['locks']}
    return [c for c in items if not locks.intersection(c['locks']) and c.get('supply_cost',0)+sum(s.get('supply_cost',0) for s in selected)<=c.get('supply_budget',10**9) and c.get('credits',0)+sum(s.get('credits',0) for s in selected)<=c.get('credit_budget',10**9) and c.get('tickets',0)+sum(s.get('tickets',0) for s in selected)<=c.get('ticket_budget',10**9)]


def select(items,limit=4):
    selected=[]
    for c in sorted(items,key=lambda c:(-c.get('policy_score',c['score']),c['id'])):
        if c in compatible([c],selected):selected.append(c)
        if len(selected)==limit:break
    return selected


def commands(obs,selected):
    return [dict(c['command'],cmd_id=obs['tick']*100+i+1,team=obs['team'],tick=obs['tick'],ttl=3000 if c['command']['op'] in (5,7) else 750) for i,c in enumerate(selected)]


def shortlist(items,limit=12):
    output=[]
    for role in ROLES:
        best=sorted((c for c in items if c['role']==role),key=lambda c:(-c.get('policy_score',c['score']),c['id']))
        if best:output.append(best[0])
    for c in sorted(items,key=lambda c:(-c.get('policy_score',c['score']),c['id'])):
        if len(output)>=limit:break
        if c not in output:output.append(c)
    return output[:limit]


class TacticalHQ:
    def __init__(self,policy=None):self.policy=policy;self.last_decision={};self.model=None;self.policy_error=False
    def ranked(self,obs):
        items=candidates(obs);policy_status='algorithm'
        if self.policy:
            try:
                from learning.candidate_policy import CandidatePolicy,vector
                if self.policy_error:raise ValueError('incompatible policy')
                if self.model is None:self.model=CandidatePolicy(self.policy)
                model=self.model;scores=model.logits(vector(obs,items))
                if not all(isfinite(float(v)) for v in scores):raise ValueError('nonfinite policy output')
                for c in items:c['policy_score']=float(scores[c['id']])
                policy_status=model.policy_id
            except (OSError,ValueError,KeyError,ImportError,TypeError,EOFError,BadZipFile):self.policy_error=True;policy_status='incompatible_policy_fallback'
        self.policy_status=policy_status;return items
    def observe_and_issue(self,obs):
        selected=select(self.ranked(obs));self.last_decision=dict(source='algorithm',policy=self.policy_status,contract=CONTRACT,reasons=[dict(unit=c['command']['unit'],candidate_id=c['id'],reason=c['reason'],score=c['score']) for c in selected])
        return commands(obs,selected)
