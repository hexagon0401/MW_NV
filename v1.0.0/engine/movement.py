"""Engine-owned movement with fractional cm retained between ticks."""
from math import hypot
from .pathfinding import find_path
from .types import WorldPos
from .orders import OrderError


def move(world, key, unit, destination, speed_mps=1.6):
    if not hasattr(world,'motions'):
        world.motions = {}
    if key not in world.motions:
        unit.task_state = 'PATH_PENDING'
        route = find_path(world.terrain,(unit.pos.x_cm,unit.pos.y_cm),destination)
        world.motions[key] = dict(route=route,x=float(unit.pos.x_cm),y=float(unit.pos.y_cm))
    motion = world.motions[key]
    route = motion['route']
    budget = speed_mps*20
    unit.task_state = 'MOVING'
    while route and budget > 0:
        x,y = motion['x'],motion['y']
        tx,ty = route[0]
        distance = hypot(tx-x,ty-y)
        amount = min(distance,budget)
        nx,ny = (tx,ty) if distance <= amount else (x+(tx-x)*amount/distance,y+(ty-y)*amount/distance)
        candidate = WorldPos(round(nx),round(ny))
        if not world.terrain.segment_clear((unit.pos.x_cm,unit.pos.y_cm),(candidate.x_cm,candidate.y_cm)):
            unit.task_state = 'BLOCKED'
            raise OrderError('BLOCKED')
        if any(s.id != unit.id and s.alive and s.carrier_id is None and
               hypot(s.pos.x_cm-candidate.x_cm,s.pos.y_cm-candidate.y_cm)<84
               for s in world.soldiers.values()):
            unit.task_state = 'BLOCKED'
            raise OrderError('BLOCKED')
        unit.pos = candidate
        motion['x'],motion['y'] = nx,ny
        budget -= amount
        if amount >= distance:
            route.pop(0)
        world.emit('UNIT_MOVED',unit=unit.id,x_cm=candidate.x_cm,y_cm=candidate.y_cm)
    if not route:
        unit.task_state = 'ARRIVED'
        world.emit('UNIT_ARRIVED',unit=unit.id)
        return True
    return False
