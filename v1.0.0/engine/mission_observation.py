"""Public task status is separate from currently observable enemy locations."""
from types import SimpleNamespace
from .sensing import can_see
from .types import WorldPos


def observed(w,team):
    mode=getattr(w,'mode','conquest');result=dict(scenario_id=getattr(w,'scenario_id','2'),mode=mode)
    from .scenario_spec import rules
    config=rules(w);result['limits']={k:config[k] for k in ('infantry_limit','vehicle_limit','credits','tickets','supply','time_limit_s')};result['limits']['score_limit']=config.get('score_limit',1)
    if mode=='conquest':return result
    own=[u for u in [*w.soldiers.values(),*w.vehicles.values()] if u.team==team and u.alive and getattr(u,'carrier_id',None) is None]
    def seen(x,y):
        target=SimpleNamespace(pos=WorldPos(x,y),alive=True,carrier_id=None)
        return any(can_see(w,u,target) for u in own)
    result['desired_roster']=getattr(w,'desired_roster',{})
    result['emplacements']=[]
    for v in w.vehicles.values():
        if v.type_id!='AA_SITE':continue
        visible=v.team==team or seen(v.pos.x_cm,v.pos.y_cm)
        result['emplacements'].append(dict(id=v.id,pos=dict(x_cm=v.pos.x_cm,y_cm=v.pos.y_cm),type_id=v.type_id,observed=visible,owner=int(v.team) if visible and v.team is not None else None,owner_known=visible,hp=v.hp if visible else None,ammo=v.ammo if visible else None,alive=v.alive if visible else None))
    result['bases']=getattr(w,'bases',{})
    result['flags']=[]
    for owner,f in getattr(w,'flags',{}).items():
        carrier=w.soldiers.get(f['carrier']) if f['carrier'] else None
        visible=f['status']=='home' or carrier is not None and carrier.team==team or f['status']=='dropped' and seen(f['x_cm'],f['y_cm']) or carrier is not None and carrier.id in getattr(w,'visible',{}).get(team,[])
        result['flags'].append(dict(owner=owner,status=f['status'],home=f['home'],position_known=bool(visible),pos=dict(x_cm=f['x_cm'],y_cm=f['y_cm']) if visible else None,carrier=f['carrier'] if visible else None,progress_ms=f['progress_ms'] if owner==team or visible else None))
    return result
