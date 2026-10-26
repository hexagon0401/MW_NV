"""Measured mission event chains; missing old telemetry is explicitly unknown."""
from collections import Counter
from math import hypot

def collect(w,initial=None):
    mode=getattr(w,'mode',None)
    if mode is None:return None
    events=w.events;counts=Counter(e['event_kind'] for e in events);first=next((e['sim_tick'] for e in events if e['event_kind']=='ABSTRACT_ATTACK'),None)
    chains=[dict(tick=e['sim_tick'],kind=e['event_kind'],**e['payload']) for e in events if e['event_kind'].startswith(('FLAG_','EMPLACEMENT_','BUILDING_'))]
    air_ids={u.id for u in w.vehicles.values() if w.vehicle_specs[u.type_id].get('aircraft',u.type_id=='HEL')}
    values={}
    for team in (0,1):
        dead=[u for u in [*w.soldiers.values(),*w.vehicles.values()] if u.team==team and not u.alive];loss=sum((w.unit_specs if u.id in w.soldiers else w.vehicle_specs)[u.type_id]['cost'] for u in dead if u.type_id!='AA_SITE')
        values[str(team)]=dict(loss_value=loss,aircraft_losses=sum(u.id in air_ids for u in dead if u.type_id!='AA_SITE'),remaining=dict(credits=w.teams[team].credits,tickets=w.teams[team].tickets,supply=w.teams[team].supply),alive_armed=sum(u.alive and u.team==team and bool((w.unit_specs if u.id in w.soldiers else w.vehicle_specs)[u.type_id]['attack']) for u in [*w.soldiers.values(),*w.vehicles.values()]))
    return dict(schema=1,game_mode=mode,scenario_id=getattr(w,'scenario_id',None),first_engagement_tick=first,events=dict(counts),objective_chain=chains,teams=values,termination_reason=getattr(w,'termination_reason',None),observation_complete=bool(initial),carrier_distance_m=sum(e['payload'].get('distance_cm',0)/100 for e in events if e['event_kind']=='FLAG_MOVED'),carrier_transport_m=sum(e['payload'].get('distance_cm',0)/100 for e in events if e['event_kind']=='FLAG_MOVED' and e['payload'].get('transport') is not None),draw_diagnostics=dict(empty_ammo_units=sum(u.alive and bool((w.unit_specs if u.id in w.soldiers else w.vehicle_specs)[u.type_id]['attack']) and u.ammo==0 for u in [*w.soldiers.values(),*w.vehicles.values()]),traffic_timeouts=sum(e['event_kind']=='ORDER_FAILED' and e['payload'].get('reason')=='TRAFFIC_TIMEOUT' for e in events),blocked_orders=sum(e['event_kind']=='ORDER_FAILED' and e['payload'].get('reason')=='BLOCKED' for e in events)),causal_claim=False)
