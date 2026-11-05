from engine.scenario import create_release_match
from engine.pathfinding import find_path
from engine.transport import FootprintTerrain
from engine.types import Team


def test_new_map_symmetry_identity_and_armor_access():
    w=create_release_match(3)
    assert (w.map_id,w.map_version)==('river-districts','2')
    assert all(row==list(reversed(row)) for row in w.terrain.cells)
    terrain=FootprintTerrain(w.terrain,w.vehicle_specs['MBT']['footprint_cm'])
    start=w.facilities[101].pos
    for f in w.facilities.values():
        if f.kind not in ('OBJECTIVE','HQ','GARAGE','HELIPAD'):continue
        assert find_path(terrain,(start.x_cm,start.y_cm),(f.pos.x_cm,f.pos.y_cm),True),f.id
    for y in (56,128,200):
        # Canonical crossings retain >=20m of navigable bridge/approach width.
        for x in range(48,66):
            assert all(w.terrain.cells[yy][x] in (0,1,7) for yy in range(y-2,y+3))


def test_spawn_roster_fits_and_distinct_districts():
    w=create_release_match(9)
    for team in Team:
        assert len([s for s in w.soldiers.values() if s.team==team])==64
        assert len([v for v in w.vehicles.values() if v.team==team])==10
    for v in w.vehicles.values():
        assert FootprintTerrain(w.terrain,w.vehicle_specs[v.type_id]['footprint_cm']).passable(v.pos.x_cm,v.pos.y_cm)
    assert sum(t==4 for row in w.terrain.cells for t in row)>400
    assert sum(t==2 for row in w.terrain.cells for t in row)>3000


def test_side_swap_reflects_every_owned_support_facility():
    normal=create_release_match(8);swapped=create_release_match(8,swap=True)
    for uid,f in normal.facilities.items():
        if f.owner is not None:
            other=swapped.facilities[uid]
            assert other.owner==f.owner
            assert other.pos.x_cm==102400-f.pos.x_cm
            assert other.pos.y_cm==f.pos.y_cm
