from engine.catalog import expanded_catalog
from engine.types import Vehicle,Emplacement,Team,WorldPos,Command,Op
from engine.runtime import Engine
from engine.capabilities import airborne,attack_allowed
from engine.emplacements import operate

def world():
    w=Engine().world;w.unit_specs,w.vehicle_specs,w.weapon_specs=expanded_catalog();return w

def test_expansion_opt_in_and_air_roles():
    w=world();bh=Vehicle(20,Team.A,WorldPos(2000,2000),'BH');bird=Vehicle(21,Team.B,WorldPos(3000,2000),'LB');aa=Vehicle(22,Team.A,WorldPos(2000,3000),'AA');w.vehicles={20:bh,21:bird,22:aa}
    bird.task_state='MOVING';assert airborne(w,bird) and attack_allowed(w,aa,bird)
    bird.task_state='IDLE';assert not attack_allowed(w,aa,bird)
    assert bh.ammo==0 and w.vehicle_specs['BH']['capacity']==8
    from engine.catalog import load_vehicles
    assert 'BH' not in load_vehicles()

def test_neutral_station_needs_crew_and_never_refills_on_capture():
    w=world();s=w.soldiers[1];station=Emplacement(50,None,s.pos);station.hp=100;station.ammo=7;w.vehicles[50]=station
    c=Command(1,Team.A,Op.OPERATE_EMPLACEMENT,unit=s.id,target=50)
    assert not attack_allowed(w,station,s)
    for _ in range(40):done=operate(w,'c',c)
    assert done and s.carrier_id==50 and station.team==Team.A and (station.hp,station.ammo)==(100,7)
    assert operate(w,'leave',c,True);assert station.team is None
