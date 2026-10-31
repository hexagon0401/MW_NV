from engine.multi_scenario import create
from engine.runtime import Engine
from engine.types import WorldPos
from agents.mission_tactics import candidates
from agents.mission_support import staging
from engine.traffic import arrival_slot

def test_both_fortresses_have_external_vehicle_staging():
    e=Engine(create(0,scenario_id='4'))
    for team in (0,1):
        obs=e.observe(team);enemy=next(f for f in obs['facilities'] if f['kind']=='HQ' and f['owner']!=team)
        goal=staging(obs,enemy['pos']);assert goal!=enemy['pos']
        for vehicle in obs['vehicles']:assert arrival_slot(obs,vehicle,goal) is not None
        rows=candidates(obs);assert rows

def test_empty_soldier_and_truck_receive_supply_candidates():
    w=create(0,scenario_id='3');e=Engine(w);u=next(s for s in w.soldiers.values() if s.team==0);u.ammo=0
    truck=next(v for v in w.vehicles.values() if v.type_id=='TRK' and v.team==0);truck.cargo_supply=0
    rows=candidates(e.observe(0))
    assert any(c['command']['unit']==u.id and c['role']=='supply' for c in rows)
    assert any(c['command']['unit']==truck.id and c['role']=='supply' for c in rows)

def test_full_dismounted_squad_enters_room_through_doors_and_steals():
    from engine.mission_rules import inside
    w=create(0,scenario_id='4');e=Engine(w);group=next(g for g in w.squads.values() if g.team==0);hq=w.facilities[102]
    for u in [*w.soldiers.values(),*w.vehicles.values()]:
        if u.team==1:u.alive=False
    for i,uid in enumerate(group.member_ids):w.soldiers[uid].pos=WorldPos(hq.pos.x_cm-4800-(i//2)*150,hq.pos.y_cm+(i%2)*150)
    group.pos=w.soldiers[group.member_ids[0]].pos
    e.submit_for(0,dict(cmd_id=1,team=0,op=18,unit=group.id,target=102,ttl=2000));e.step(90)
    assert sum(inside(w.soldiers[i].pos,w.bases[1]['room']) for i in group.member_ids)>=3
    assert w.teams[0].score==1
