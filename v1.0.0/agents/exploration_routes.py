"""Bounded weighted routes using permitted terrain and currently observed threats."""
from copy import deepcopy
from collections import defaultdict
import heapq,math

GROUPS={'capture':'mission','defend':'mission','flag':'mission','infiltrate':'mission','return':'mission','recover':'mission','intercept':'mission','attack':'combat','anti_armor':'combat','anti_air':'combat','fire':'combat','recon':'maneuver','transport':'maneuver','retreat':'maneuver','supply':'logistics','repair':'logistics'}


def route(obs,actor,goal,style,max_nodes=20000):
    cells=obs['terrain'];height=len(cells);width=len(cells[0]);vehicle=actor.get('type_id') in obs['catalog']['vehicles'];spec=(obs['catalog']['vehicles'] if vehicle else obs['catalog']['units'])[actor['type_id']]
    start=(actor['pos']['x_cm']//400,actor['pos']['y_cm']//400);end=(goal[0]//400,goal[1]//400)
    air=bool(spec.get('aircraft',actor['type_id']=='HEL'))
    footprint=spec.get('footprint_cm',[100,100])
    allowed=(0,1,7,8) if vehicle else (0,1,2,4,5,7,8,10)
    def legal(p):
        x,y=p
        if not(0<=x<width and 0<=y<height):return False
        if air:return True
        if not vehicle:return cells[y][x] in allowed
        cx,cy=x*400+200,y*400+200;hw,hh=footprint[0]//2,footprint[1]//2
        left,right=(cx-hw)//400,(cx+hw-1)//400;top,bottom=(cy-hh)//400,(cy+hh-1)//400
        return 0<=left<=right<width and 0<=top<=bottom<height and all(cells[cy][cx] in allowed for cy in range(top,bottom+1) for cx in range(left,right+1))
    if not legal(start) or not legal(end):return None
    threats=[(e['pos']['x_cm']/400,e['pos']['y_cm']/400) for e in obs['enemies']]
    def risk(p):return min(1,sum(max(0,1-math.hypot(p[0]-x,p[1]-y)/25) for x,y in threats))
    heap=[(0,start)];cost={start:0};parent={};visited=0
    while heap and visited<max_nodes:
        _,p=heapq.heappop(heap);visited+=1
        if p==end:
            path=[p]
            while path[-1]!=start:path.append(parent[path[-1]])
            path.reverse();points=[(x*400+200,y*400+200) for x,y in path];length=sum(math.dist(a,b) for a,b in zip(points,points[1:]))/100
            return points,dict(path_length_m=length,risk=sum(map(risk,path))/len(path),cover=sum(cells[y][x]==2 for x,y in path)/len(path),unexplored=None)
        for q in ((p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1)):
            if not legal(q):continue
            step=1+(4*risk(q) if style=='avoid' else 0)+(1.5 if style=='cover' and cells[q[1]][q[0]]!=2 else 0)
            value=cost[p]+step
            if value<cost.get(q,float('inf')):
                cost[q]=value;parent[q]=p;heapq.heappush(heap,(value+abs(q[0]-end[0])+abs(q[1]-end[1]),q))
    return None


def balanced(items):
    buckets=defaultdict(lambda:defaultdict(list))
    for c in items:buckets[GROUPS.get(c['role'],'maneuver')][c['command']['unit']].append(c)
    queues={}
    for group,actors in buckets.items():
        for rows in actors.values():rows.sort(key=lambda c:(-c['score'],c.get('analysis',{}).get('route_style',''),str(c['command'])))
        queues[group]=[actors[a][i] for i in range(max(map(len,actors.values()))) for a in sorted(actors) if i<len(actors[a])]
    result=[]
    for group in ('mission','combat','maneuver','logistics'):result.extend(queues.get(group,[])[:16]);queues[group]=queues.get(group,[])[16:]
    while len(result)<64 and any(queues.values()):
        for group in sorted(queues):
            if queues[group] and len(result)<64:result.append(queues[group].pop(0))
    for i,c in enumerate(result):c['id']=i
    return result


def candidates(obs):
    from .mission_tactics import candidates as base
    items=deepcopy(base(obs));actors={u['id']:u for u in obs['units']+obs['vehicles']}
    for squad in obs['squads']:
        members=[actors[i] for i in squad['member_ids'] if i in actors and actors[i]['alive'] and actors[i].get('carrier_id') is None]
        if members:actors[squad['id']]=members[0]
    evaluated=0
    for c in list(items):
        cmd=c['command'];actor=actors.get(cmd['unit'])
        if cmd['op'] not in (2,7,10) or not actor or evaluated>=4:continue
        if any(o['unit']==cmd['unit'] and o['status'] in ('QUEUED','RUNNING') for o in obs.get('orders',[])):continue
        goal=(cmd['arg0']*100,cmd['arg1']*100);evaluated+=1;seen=set()
        for style in ('shortest','avoid','cover'):
            found=route(obs,actor,goal,style)
            if not found:continue
            points,info=found
            # Bound each leg; future HQ decisions choose subsequent route legs.
            waypoint=points[min(20,len(points)-1)];key=waypoint
            if key in seen:continue
            seen.add(key);copy=deepcopy(c);copy['command'].update(arg0=waypoint[0]//100,arg1=waypoint[1]//100)
            spec=(obs['catalog']['vehicles'] if actor['type_id'] in obs['catalog']['vehicles'] else obs['catalog']['units'])[actor['type_id']]
            copy['analysis'].update(info,route_style=style,route_goal=goal,eta_s=info['path_length_m']/max(.1,spec.get('speed_mps',1.6)))
            hq=next((f for f in obs['facilities'] if f['kind']=='HQ' and f['owner']==obs['team']),None)
            gx=waypoint[0]/(obs['map_width_m']*100)
            copy['features'][14:16]=[1-gx if hq and hq['pos']['x_cm']>obs['map_width_m']*50 else gx,waypoint[1]/(obs['map_height_m']*100)]
            copy['reason']+=' · '+style+' 경로 경유';items.append(copy)
    return balanced(items)
