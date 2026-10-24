from engine.state import WorldState


def test_seed_clone_checksum():
    a, b, c = WorldState(4), WorldState(4), WorldState(5)
    assert a.checksum() == b.checksum()
    assert a.map_sample != c.map_sample
    clone = a.clone()
    assert clone.checksum() == a.checksum()
    clone.soldiers[1].hp = 30
    assert a.soldiers[1].hp == 100
    clone = a.clone()
    assert clone.rng.random() == a.rng.random()
    assert clone.checksum() == a.checksum()
