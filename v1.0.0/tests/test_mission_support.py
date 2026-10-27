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
