"""Capability checks shared by combat, transport, observations and policies."""
FLYING=('TAKEOFF','MOVING','LANDING','HOVERING')
def aircraft(world,unit):return unit.id in world.vehicles and (world.vehicle_specs[unit.type_id].get('aircraft',False) or unit.type_id=='HEL')
def airborne(world,unit):
    if not aircraft(world,unit):return False
    if unit.task_state in FLYING:return True
    # Older checkpoints may label a cancelled flight READY/HOLD over water.
    # Recover from the latest flight journal, never from the terrain alone.
    queue=getattr(world,'queue',None)
    for key,flight in reversed(getattr(world,'flights',{}).items()):
        command=getattr(queue,'commands',{}).get(key)
        if command is None or command.unit!=unit.id:continue
        return (getattr(queue,'status',{}).get(key)!='COMPLETED' and flight['stage'] in FLYING
                and (unit.pos.x_cm,unit.pos.y_cm)==(round(flight['x']),round(flight['y'])))
    return False
def enabled(world,unit):
    if not getattr(unit,'alive',False) or unit.team is None:return False
    crew=getattr(unit,'crew_id',None)
    return unit.type_id!='AA_SITE' or crew in world.soldiers and world.soldiers[crew].alive and world.soldiers[crew].carrier_id==unit.id

def attack_allowed(world,attacker,target):
    if not enabled(world,attacker):return False
    spec=(world.unit_specs if attacker.id in world.soldiers else world.vehicle_specs)[attacker.type_id]
    return not spec.get('air_only',False) or airborne(world,target)
