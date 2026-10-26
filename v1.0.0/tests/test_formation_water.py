import pytest
from engine.runtime import Engine
from engine.map import Terrain,Tile
from engine.types import Squad,Team,WorldPos
from engine.catalog import make_soldier
from engine.infantry import move_squad
from engine.orders import OrderError

@pytest.mark.parametrize('mirror',[False,True])
def test_all_members_cross_narrow_bridge_without_entering_water(mirror):
    e=Engine();w=e.world;w.soldiers.clear();w.squads.clear();w.terrain=Terrain(128,128)
    # A narrow north/south bridge cannot admit the original east/west formation.
    for row in range(10,18):
        for col in range(w.terrain.cols):w.terrain.set_tile(col,row,Tile.DEEP_WATER)
    for row in range(10,18):w.terrain.set_tile(16,row,Tile.BRIDGE)
    for i in range(8):
        x=6000+i*150;x=12800-x if mirror else x
        w.soldiers[i+1]=make_soldier(i+1,Team.A,WorldPos(x,3000),'INF',w.unit_specs)
    squad=Squad(30,Team.A,w.soldiers[1].pos,list(w.soldiers));w.squads[30]=squad
    for tick in range(3000):
        w.tick=tick;before={s.id:s.pos for s in w.soldiers.values()}
        done=move_squad(w,'cross',squad,(6600,9000),engage=False)
        for s in w.soldiers.values():
            assert w.terrain.segment_clear((before[s.id].x_cm,before[s.id].y_cm),(s.pos.x_cm,s.pos.y_cm))
            assert abs(s.pos.x_cm-before[s.id].x_cm)<=32 and abs(s.pos.y_cm-before[s.id].y_cm)<=32
        if done:break
    assert done
    assert all(s.pos.y_cm>7200 for s in w.soldiers.values())
    assert len({s.pos for s in w.soldiers.values()})==8
    assert any(e['event_kind']=='FORMATION_COLUMN' for e in w.events)

def test_impossible_goal_fails_bounded_and_records_cooldown():
    e=Engine();w=e.world;s=next(iter(w.soldiers.values()));w.soldiers={s.id:s};g=Squad(30,s.team,s.pos,[s.id]);w.squads={30:g}
    w.terrain.set_tile(10,10,Tile.DEEP_WATER)
    for tick in range(3):
        w.tick=tick
        try:move_squad(w,'bad',g,(4200,4200),engage=False)
        except OrderError as exc:assert str(exc)=='FORMATION_UNREACHABLE';break
    else:pytest.fail('unreachable command did not terminate')
    assert w.failed_goals[-1]['until_tick']==152
