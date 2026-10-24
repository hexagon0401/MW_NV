from engine.runtime import Engine
from engine.state import WorldState
from engine.types import WorldPos


def encounter(role='INF',ammo=30):
    e=Engine(WorldState(15));a,b=e.world.soldiers.values()
    a.pos=WorldPos(1000,6400);b.pos=WorldPos(2000,6400)
    a.type_id=role;a.ammo=ammo;b.ammo=0
    e.step(40)
    return e.world


def test_damage_reproducible_and_disabled():
    a,b=encounter(),encounter()
    assert a.checksum()==b.checksum()
    attacks=[e for e in a.events if e['event_kind']=='ABSTRACT_ATTACK']
    assert attacks and any(e['payload']['damage']==11 for e in attacks)
    assert all(b['sim_tick']-a['sim_tick']>=10 for a,b in zip(attacks,attacks[1:]))
    assert 0<=a.soldiers[2].hp<100


def test_noncombatants_and_empty_ammo():
    for role,ammo in [('MED',30),('ENG',30),('INF',0)]:
        w=encounter(role,ammo)
        assert not any(e['event_kind']=='ABSTRACT_ATTACK' for e in w.events)
