from engine.runtime import Engine
from engine.types import Team
from engine.orders import OrderError
import pytest


def test_purchase_debits_once_and_respects_ownership_and_budget():
    e=Engine();w=e.world;before=w.teams[Team.A].credits
    raw=dict(cmd_id=1,team=0,op=11,arg0=4,target=101)
    e.submit(raw);e.submit(raw);e.step()
    spawned=[s for s in w.soldiers.values() if s.type_id=='ENG']
    assert len(spawned)==1 and w.teams[Team.A].credits==before-25
    assert w.teams[Team.A].tickets==69
    with pytest.raises(OrderError,match='FOREIGN_UNIT'):
        e.submit(dict(cmd_id=2,team=0,op=11,arg0=5,target=102))
    e.step()
    assert len(w.vehicles)==0
    w.teams[Team.A].credits=0
    e.submit(dict(cmd_id=3,team=0,op=11,arg0=5,target=101));e.step()
    assert len(w.vehicles)==0 and w.teams[Team.A].tickets==69
