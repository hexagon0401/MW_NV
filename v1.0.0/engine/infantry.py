"""Footprint-aware formations with bounded, physical single-file recovery."""
from copy import deepcopy
from math import hypot,atan2,cos,sin,pi
from .movement import move
from .pathfinding import find_path
from .orders import OrderError
from .types import WorldPos


def _column(w,key,members,destination):
    # Every member joins one shared spine, then walks to a distinct legal end slot.
    leader=members[0];start=(leader.pos.x_cm,leader.pos.y_cm)
    spine=find_path(w.terrain,start,destination)
    used=[];plans={};vx=destination[0]-start[0];vy=destination[1]-start[1]
    for i,s in enumerate(members):
        slots=[(destination[0]+dx,destination[1]+dy) for radius in range(0,1201,150) for dx,dy in ((-radius,0),(radius,0),(0,-radius),(0,radius)) if dx*vx+dy*vy<=0]
        slot=next((p for p in slots if w.terrain.passable(*p) and all(hypot(p[0]-x,p[1]-y)>=100 for x,y in used) and w.terrain.segment_clear(destination,p)),None)
        if slot is None:raise OrderError('FORMATION_NO_ARRIVAL_SLOT')
        used.append(slot)
        plans[f'{key}:member:{s.id}']=dict(route=find_path(w.terrain,(s.pos.x_cm,s.pos.y_cm),slot),x=float(s.pos.x_cm),y=float(s.pos.y_cm))
    w.motions.update(plans)
    w.emit('FORMATION_COLUMN',squad=members[0].squad_id,members=[s.id for s in members])


def move_squad(w,key,squad,destination,engage=True):
    members=[w.soldiers[i] for i in squad.member_ids if i in w.soldiers and w.soldiers[i].alive and not (w.soldiers[i].carrier_id in w.vehicles and w.vehicles[w.soldiers[i].carrier_id].type_id=='AA_SITE')]
    if not members or any(s.team!=squad.team or s.carrier_id is not None for s in members):raise OrderError('ILLEGAL_STATE')
    if not hasattr(w,'squad_navigation'):w.squad_navigation={}
    state=w.squad_navigation.setdefault(key,dict(mode='formation',attempts=0,last_progress=w.tick,positions={},members=[]))
    from .combat import engagement_target
    if engage and any(engagement_target(w,s) is not None for s in members):
        state['last_progress']=w.tick
        for s in members:s.task_state='ENGAGING'
        return False
    ids=[s.id for s in members]
    if state['members']!=ids:
        state['members']=ids;state['planned']=False
        w.motions=getattr(w,'motions',{})
        w.motions.pop(key,None)
    leader=members[0]
    from .mission_actions import speed as mission_speed
    speed=min(mission_speed(w,s,w.unit_specs[s.type_id]['speed_mps']) for s in members)
    old={s.id:s.pos for s in members};previous=deepcopy(getattr(w,'motions',{}).get(key));event_count=len(w.events)
    try:
        if state['mode']=='formation':
            offsets=[(s.pos.x_cm-leader.pos.x_cm,s.pos.y_cm-leader.pos.y_cm) for s in members]
            done=move(w,key,leader,destination,speed,squad.member_ids,offsets)
            dx,dy=leader.pos.x_cm-old[leader.id].x_cm,leader.pos.y_cm-old[leader.id].y_cm
            for s in members:
                p=WorldPos(old[s.id].x_cm+dx,old[s.id].y_cm+dy)
                if not w.terrain.segment_clear((old[s.id].x_cm,old[s.id].y_cm),(p.x_cm,p.y_cm)):raise OrderError('BLOCKED')
                if any(o.id not in ids and o.alive and o.carrier_id is None and hypot(o.pos.x_cm-p.x_cm,o.pos.y_cm-p.y_cm)<84 for o in w.soldiers.values()):raise OrderError('BLOCKED')
            for s in members:
                s.pos=WorldPos(old[s.id].x_cm+dx,old[s.id].y_cm+dy);s.task_state=leader.task_state
                if s is not leader:w.emit('UNIT_MOVED',unit=s.id,x_cm=s.pos.x_cm,y_cm=s.pos.y_cm)
        else:
            if not state.get('planned'):_column(w,key,members,destination);state['planned']=True
            done=True
            for s in members:
                member_key=f'{key}:member:{s.id}'
                try:
                    motion=w.motions[member_key];route=motion['route'];arrived=not route
                    if len(route)>1 and w.terrain.segment_clear((s.pos.x_cm,s.pos.y_cm),route[-1]):route[:]=[route[-1]]
                    while len(route)>1 and hypot(s.pos.x_cm-route[0][0],s.pos.y_cm-route[0][1])<=110:route.pop(0)
                    if route:
                        tx,ty=route[0];distance=hypot(tx-s.pos.x_cm,ty-s.pos.y_cm)
                        angle=atan2(ty-s.pos.y_cm,tx-s.pos.x_cm);budget=min(speed*20,distance)
                        choices=[]
                        for turn in (0,pi/4,-pi/4,pi/2,-pi/2):
                            x=round(s.pos.x_cm+cos(angle+turn)*budget);y=round(s.pos.y_cm+sin(angle+turn)*budget)
                            if not w.terrain.segment_clear((s.pos.x_cm,s.pos.y_cm),(x,y)):continue
                            if any(o.id!=s.id and o.alive and o.carrier_id is None and hypot(o.pos.x_cm-x,o.pos.y_cm-y)<84 for o in w.soldiers.values()):continue
                            choices.append((hypot(tx-x,ty-y),abs(turn),x,y))
                        if choices:
                            _,_,x,y=min(choices);s.pos=WorldPos(x,y);s.task_state='MOVING';motion['x']=x;motion['y']=y
                            w.emit('UNIT_MOVED',unit=s.id,x_cm=x,y_cm=y)
                            if hypot(tx-x,ty-y)<1:route.pop(0)
                        else:s.task_state='WAITING_FORMATION'
                        arrived=not route
                    done=done and arrived
                except OrderError:
                    s.task_state='WAITING_FORMATION';done=False
        squad.pos=leader.pos
        moved=sum(hypot(s.pos.x_cm-old[s.id].x_cm,s.pos.y_cm-old[s.id].y_cm) for s in members)
        remaining=0
        if state['mode']=='column':
            for s in members:
                route=w.motions.get(f'{key}:member:{s.id}',{}).get('route',[])
                points=[(s.pos.x_cm,s.pos.y_cm),*route]
                remaining+=sum(hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(points,points[1:]))
        else:remaining=hypot(leader.pos.x_cm-destination[0],leader.pos.y_cm-destination[1])
        if remaining<state.get('best_remaining',float('inf'))-30:state['last_progress']=w.tick;state['best_remaining']=remaining
        if done:
            # Re-form only through individually validated physical routes; end slots never overlap.
            w.emit('FORMATION_ARRIVED',squad=squad.id,mode=state['mode']);return True
        if w.tick-state['last_progress']>=75:raise OrderError('FORMATION_STALLED')
        return False
    except OrderError as exc:
        if state['mode']=='formation':
            for s in members:s.pos=old[s.id]
            del w.events[event_count:]
            if previous is None:getattr(w,'motions',{}).pop(key,None)
            else:w.motions[key]=previous
        state['mode']='column';state['planned']=False;state.pop('best_remaining',None)
        if state['attempts']<2:
            state['attempts']+=1;state['last_progress']=w.tick
            for s in members:s.task_state='WAITING_FORMATION'
            w.emit('FORMATION_REPLAN',squad=squad.id,attempt=state['attempts'],reason=str(exc));return False
        if not hasattr(w,'failed_goals'):w.failed_goals=[]
        w.failed_goals.append(dict(team=int(squad.team),unit=squad.id,x_cm=destination[0],y_cm=destination[1],until_tick=w.tick+150,terrain_revision=w.terrain.revision))
        raise OrderError('FORMATION_UNREACHABLE') from exc
