import pytest
from engine.scenario import create_release_match
from engine.catalog import catalog_document
from engine.types import Team,Vehicle,WorldPos
from engine.runtime import Engine
from engine.logistics import repair
from engine.types import Command,Op


def test_full_release_roster_and_catalog():
    w=create_release_match(2);catalog=catalog_document()
    for team in Team:
        assert sum(s.team==team for s in w.soldiers.values())==64
        assert sum(v.team==team for v in w.vehicles.values())==10
        assert sum(g.team==team and len(g.member_ids)==8 for g in w.squads.values())==8
        assert (w.teams[team].credits,w.teams[team].tickets,w.teams[team].supply)==(1000,32,600)
    ids=[u.id for collection in (w.soldiers,w.vehicles,w.squads,w.facilities) for u in collection.values()]
    assert len(ids)==len(set(ids))
    assert catalog['vehicles']['MBT']['hp']==900
    assert catalog['vehicles']['HEL']['capacity']==16
    assert catalog['weapons']['multipliers']['rifle']['heavy']==0
    for v in w.vehicles.values():
        assert w.terrain.passable(v.pos.x_cm,v.pos.y_cm,True)
        assert v.hp==w.vehicle_specs[v.type_id]['hp']


def test_engineer_repairs_and_supplies_ammo():
    w=create_release_match();eng=next(s for s in w.soldiers.values() if s.type_id=='ENG' and s.team==0)
    tank=next(v for v in w.vehicles.values() if v.type_id=='MBT' and v.team==0)
    eng.pos=tank.pos;tank.hp-=30
    c=Command(1,Team.A,Op.REPAIR,unit=eng.id,target=tank.id)
    before=w.teams[0].supply
    for _ in range(10):repair(w,'r',c)
    assert tank.hp==880 and before-w.teams[0].supply==2 and eng.repair_pool==40
