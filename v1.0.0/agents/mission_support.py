"""Public-observation-only staging, logistics and coverage goals."""
from math import hypot,cos,sin,pi
from engine.map import Terrain
from engine.transport import FootprintTerrain


def staging(obs,goal):
    """Never ask vehicle parking to originate inside an infantry-only fortress."""
    hq=next((f for f in obs['facilities'] if f['kind']=='HQ' and f['pos']==goal),None)
    if obs['mission']['mode']!='capture_flag' or hq is None:return goal
    direction=1 if goal['x_cm']<obs['map_width_m']*50 else -1
    terrain=Terrain(obs['map_width_m'],obs['map_height_m']);terrain.cells=obs['terrain'];footprint=FootprintTerrain(terrain,[1000,1000])
    for radius in (8000,9600,6400,11200):
        for dx,dy in ((direction,0),(direction,-1),(direction,1),(0,-1),(0,1)):
            x=goal['x_cm']+dx*radius;y=goal['y_cm']+dy*radius
            if footprint.passable(x,y):return dict(x_cm=x,y_cm=y)
    return dict(x_cm=goal['x_cm']+direction*8000,y_cm=goal['y_cm'])


def logistics(obs,add):
    catalog=obs['catalog'];vehicles=[v for v in obs['vehicles'] if v['alive']]
    depots=[f for f in obs['facilities'] if f['owner']==obs['team'] and f['kind'] in ('HQ','SUPPLY_NODE')]
    trucks=[v for v in vehicles if v['type_id']=='TRK']
    own=[u for u in obs['units'] if u['alive'] and u['carrier_id'] is None]
    terrain=Terrain(obs['map_width_m'],obs['map_height_m']);terrain.cells=obs['terrain']
    def distance(a,b):return hypot(a['pos']['x_cm']-b['pos']['x_cm'],a['pos']['y_cm']-b['pos']['y_cm'])
    def near(a,b):
        dx=abs(a['pos']['x_cm']-b['pos']['x_cm']);dy=abs(a['pos']['y_cm']-b['pos']['y_cm'])
        if b.get('type_id')=='TRK':
            angle=b.get('heading',0) or 0;rx=(a['pos']['x_cm']-b['pos']['x_cm'])*cos(angle)+(a['pos']['y_cm']-b['pos']['y_cm'])*sin(angle);ry=-(a['pos']['x_cm']-b['pos']['x_cm'])*sin(angle)+(a['pos']['y_cm']-b['pos']['y_cm'])*cos(angle)
            length,width=catalog['vehicles']['TRK']['footprint_cm'];extra=catalog['vehicles'][a['type_id']]['footprint_cm'] if a in vehicles else (0,0);dx=max(0,abs(rx)-(length+extra[0])/2);dy=max(0,abs(ry)-(width+extra[1])/2)
        return hypot(dx,dy)<= (2300 if b.get('kind')=='HQ' and obs['mission']['mode']=='capture_flag' else 300)
    needy=[]
    for actor in [*own,*vehicles]:
        spec=(catalog['units'] if actor in own else catalog['vehicles'])[actor['type_id']]
        low=spec['ammo']>0 and actor['ammo']<=spec['ammo']*.25
        reload_truck=actor.get('type_id')=='TRK' and actor.get('cargo_supply',0)<spec['cargo_capacity']*.25
        if not low and not reload_truck and not (actor in vehicles and actor['fuel']<20):continue
        needy.append(actor)
        if actor.get('carrier_id') is not None or actor['task_state'] in ('RESUPPLYING','TAKEOFF','LANDING','UNLOADING','WAITING_PASSENGERS'):continue
        nodes=[*depots,*[t for t in trucks if t['id']!=actor['id'] and t.get('cargo_supply',0)>=2 and not reload_truck]]
        nodes=[n for n in nodes if n.get('type_id')=='TRK' or obs['resources']['supply']>0]
        node=min(nodes,key=lambda n:(distance(actor,n),n['id']),default=None)
        if node is None:continue
        priority=195 if spec['ammo'] and actor['ammo']==0 else 170
        if near(actor,node):add(actor,'supply',8,node['pos'],priority,target=node['id'],reason='현장 보급·탄약/연료/적재 회복',locks=[node['id']] if node.get('type_id')=='TRK' else [])
        elif actor.get('deployment') not in (None,'PACKED'):add(actor,'supply',16,actor['pos'],priority,reason='재보급 전 포병 철수')
        else:
            footprint=FootprintTerrain(terrain,spec['footprint_cm']) if actor in vehicles else terrain
            radius=2000 if node.get('kind')=='HQ' and obs['mission']['mode']=='capture_flag' else (900 if actor in vehicles else 600) if node.get('type_id')=='TRK' else 200
            positions=[]
            for i in range(16):
                angle=2*pi*((i+actor['id'])%16)/16;x=round((node['pos']['x_cm']+cos(angle)*radius)/100)*100;y=round((node['pos']['y_cm']+sin(angle)*radius)/100)*100
                if footprint.passable(x,y):positions.append(dict(x_cm=x,y_cm=y))
            if positions:
                goal=min(positions,key=lambda p:(hypot(p['x_cm']-actor['pos']['x_cm'],p['y_cm']-actor['pos']['y_cm']),p['x_cm'],p['y_cm']))
                add(actor,'supply',7 if actor in vehicles else 2,goal,priority,reason='HQ/보급차 재보급 접근')
    for truck in trucks:
        if truck.get('cargo_supply',0)<2 or truck['task_state'] in ('MOVING','RESUPPLYING'):continue
        target=min((u for u in needy if u['id']!=truck['id']),key=lambda u:(distance(truck,u),u['id']),default=None)
        if target and distance(truck,target)>2000:
            from engine.traffic import arrival_slot
            slot=arrival_slot(obs,truck,target['pos'])
            if slot:add(truck,'supply',7,dict(x_cm=slot[0]*100,y_cm=slot[1]*100),165,reason='탄약 부족 부대 현장 지원')


def search_goals(obs,squad):
    # Deterministic complete grid cycle, phased by squad; does not inspect enemy state.
    terrain=obs.get('terrain');result=[];phase=obs['tick']//300+squad['id']
    for j in range(25):
        cell=(phase+j)%25;x=round(obs['map_width_m']*(cell%5+.5)/5);y=round(obs['map_height_m']*(cell//5+.5)/5)
        if terrain[y//4][x//4] in (0,1,2,5,7,8):result.append(dict(x_cm=x*100,y_cm=y*100))
        if len(result)==3:break
    return result
