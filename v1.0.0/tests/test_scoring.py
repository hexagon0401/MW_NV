from engine.runtime import Engine
from engine.types import Team,Facility,WorldPos


def test_score_limit_and_idempotent_end():
    e=Engine();w=e.world
    w.facilities={100:Facility(100,WorldPos(5000,5000),owner=Team.A)}
    w.teams[Team.A].score=98;w.tick=148
    e.step(.2);assert w.teams[Team.A].score==98
    e.step(.2);assert w.teams[Team.A].score==100 and w.winner==Team.A
    checksum=w.checksum();e.step(5);assert w.checksum()==checksum


def test_time_limit_and_full_overtime_boundary():
    e=Engine();w=e.world;w.tick=13498;w.teams[Team.B].score=1
    e.step(.2);assert not w.ended
    e.step(.2);assert w.ended and w.winner==Team.B
    e=Engine();w=e.world;w.tick=13499;e.step(.2)
    assert w.overtime and not w.ended
    w.tick=14998;e.step(.2);assert not w.ended
    e.step(.2);assert w.ended and w.winner is None
