"""Formation translation at the slowest living member's speed."""
from copy import deepcopy
from math import hypot
from .movement import move
from .orders import OrderError
from .types import WorldPos


def move_squad(w,key,squad,destination,engage=True):
    members=[w.soldiers[i] for i in squad.member_ids if i in w.soldiers and w.soldiers[i].alive]
    if not members or any(s.team != squad.team or s.carrier_id is not None for s in members):
        raise OrderError('ILLEGAL_STATE')
    from .combat import engagement_target
    if engage and any(engagement_target(w,s) is not None for s in members):
        for s in members:s.task_state='ENGAGING'
        return False
    leader=members[0]
    old={s.id:s.pos for s in members}
    previous=deepcopy(getattr(w,'motions',{}).get(key))
    event_count=len(w.events)
    try:
        done=move(w,key,leader,destination,min(w.unit_specs[s.type_id]['speed_mps'] for s in members),squad.member_ids)
        dx,dy=leader.pos.x_cm-old[leader.id].x_cm,leader.pos.y_cm-old[leader.id].y_cm
        candidates={s.id:(old[s.id].x_cm+dx,old[s.id].y_cm+dy) for s in members}
        for s in members:
            x,y=candidates[s.id]
            if not w.terrain.segment_clear((old[s.id].x_cm,old[s.id].y_cm),(x,y)):
                raise OrderError('BLOCKED')
            if any(o.id not in squad.member_ids and o.alive and o.carrier_id is None and hypot(o.pos.x_cm-x,o.pos.y_cm-y)<84 for o in w.soldiers.values()):
                raise OrderError('BLOCKED')
        for s in members:
            s.pos=WorldPos(*candidates[s.id]);s.task_state=leader.task_state
            if s is not leader:
                w.emit('UNIT_MOVED',unit=s.id,x_cm=s.pos.x_cm,y_cm=s.pos.y_cm)
        squad.pos=leader.pos
        return done
    except OrderError:
        for s in members:
            s.pos=old[s.id];s.task_state='BLOCKED'
        del w.events[event_count:]
        if previous is None:
            w.motions.pop(key,None)
        else:
            w.motions[key]=previous
        raise
