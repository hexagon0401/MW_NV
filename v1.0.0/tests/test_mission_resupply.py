from engine.runtime import Engine
from engine.types import Team
from engine.logistics import resupply
from engine.types import Command,Op

def test_partial_ammo_finite_stock_and_authoritative_event():
    e=Engine();w=e.world;u=w.soldiers[1];u.ammo=0;w.teams[Team.A].supply=2
    e.submit(dict(cmd_id=1,team=0,op=8,unit=1,target=101));e.step(4)
    assert u.ammo==10 and w.teams[Team.A].supply==0
    assert any(x['event_kind']=='UNIT_RESUPPLIED' and x['payload']['ammo']==10 for x in w.events)
