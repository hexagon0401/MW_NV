"""Engine-owned victory dispatch; map generation never determines a winner."""
from .scenario_spec import rules
from .objectives import update_capture,update_score

def update(world):
    mode=rules(world)['mode']
    if mode=='conquest':
        update_capture(world);update_score(world)
    elif mode in ('elimination','capture_flag'):
        from .mission_rules import update as mission_update
        mission_update(world)
    else:raise ValueError('unsupported scenario mode')

def end(world,winner,reason):
    if getattr(world,'ended',False):return
    world.ended=True;world.winner=winner;world.termination_reason=reason
    world.emit('MATCH_ENDED',winner=None if winner is None else int(winner),reason=reason,mode=rules(world)['mode'])
