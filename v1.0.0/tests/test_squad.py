from engine.runtime import Engine
from engine.catalog import make_soldier
from engine.types import Squad,Team,WorldPos


def test_five_members_follow_slowest_without_id_or_position_duplicates():
    e=Engine();w=e.world;w.soldiers.clear()
    for i,t in enumerate(('INF','INF','SUP','MED','INF'),1):
        w.soldiers[i]=make_soldier(i,Team.A,WorldPos(1000-(i//2)*150,6000+(i%2)*150),t)
    group=Squad(20,Team.A,w.soldiers[1].pos,list(w.soldiers))
    w.squads[20]=group
    start={i:s.pos for i,s in w.soldiers.items()}
    e.submit(dict(cmd_id=1,team=0,op=2,unit=20,arg0=50,arg1=61))
    e.step(10)
    assert len({s.pos for s in w.soldiers.values()})==5
    for i,s in w.soldiers.items():
        assert 1290 <= s.pos.x_cm-start[i].x_cm <= 1300
        assert w.terrain.inside(s.pos.x_cm,s.pos.y_cm)
    assert group.pos==w.soldiers[1].pos
