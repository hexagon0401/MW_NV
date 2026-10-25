from engine.scenario import create_release_match
from engine.runtime import Engine
from engine.sensing import update_sensing
from engine.types import WorldPos,Team
from agents.tactics import candidates


def test_candidates_skip_tank_friendly_blast_risk_and_ignore_hidden_positions():
    w=create_release_match(0);e=Engine(w)
    tank=next(v for v in w.vehicles.values() if v.type_id=='MBT' and v.team==0);tank.pos=WorldPos(45000,51200)
    foe=next(s for s in w.soldiers.values() if s.team==1);foe.pos=WorldPos(48000,51200)
    friend=next(s for s in w.soldiers.values() if s.team==0);friend.pos=WorldPos(48000,51300)
    # Clear direct-fire LOS and keep the enemy visible.
    for y in range(125,131):
        for x in range(109,123):w.terrain.cells[y][x]=0
    update_sensing(w);obs=e.observe(Team.A);items=candidates(obs)
    assert not any(c['command']['unit']==tank.id and c['command']['op']==13 and c['command']['target']==foe.id for c in items)
    hidden=next(s for s in w.soldiers.values() if s.team==1 and s.id not in w.visible[Team.A]);hidden.pos=WorldPos(90000,90000)
    assert items==candidates(e.observe(Team.A))
