import pytest
from engine.scenario_spec import specification,attach
from engine.scenario import create_release_match
from engine.runtime import Engine
from engine.logistics import regenerate
from engine.types import Team

def test_scenario_catalog_isolated_and_limits():
    a=specification(3);assert (a['width_m'],a['height_m'],a['infantry_limit'],a['vehicle_limit'])==(1536,1536,128,22)
    a['credits']=0;assert specification(3)['credits']==3000
    assert specification(4)['mode']=='capture_flag' and specification(4)['width_m']==2304

def test_legacy_conquest_dispatch_matches_original():
    from engine.objectives import update_capture,update_score
    from engine.mode_rules import update
    w=create_release_match(41);other=w.clone();w.tick=149;other.tick=149
    update(w);update_capture(other);update_score(other)
    assert w.checksum()==other.checksum()

def test_new_modes_do_not_generate_infinite_supply():
    w=attach(create_release_match(),3);w.tick=299;before=w.teams[Team.A].supply;regenerate(w);assert w.teams[Team.A].supply==before
    del w.scenario;regenerate(w);assert w.teams[Team.A].supply>before
