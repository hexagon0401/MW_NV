from engine.scenario import create_release_match
from engine.types import Team
from engine.sensing import update_sensing,can_see


def test_release_map_scale_and_reflection():
    w=create_release_match(3)
    assert w.config.map_width_m==1024
    assert w.facilities[201].pos.x_cm==51200
    assert w.facilities[203].pos.y_cm==80000
    assert w.facilities[307].pos.x_cm==15200
    assert all(row==list(reversed(row)) for row in w.terrain.cells)


def test_spatial_visibility_matches_reference_scan():
    w=create_release_match(8)
    update_sensing(w)
    for team in Team:
        expected=sorted(t.id for t in w.soldiers.values() if t.team!=team and any(can_see(w,s,t) for s in w.soldiers.values() if s.team==team))
        assert w.visible[team]==expected
