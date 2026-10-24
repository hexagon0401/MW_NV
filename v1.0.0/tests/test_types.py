import json
import pytest
from engine.types import Soldier, Squad, Team, WorldPos


def test_entity_serialization_and_independent_members():
    s = Soldier(1, Team.A, WorldPos(120, 300))
    assert json.loads(json.dumps(s.to_dict()))['pos'] == {'x_cm': 120, 'y_cm': 300}
    assert s.to_dict()['team'] == 0


@pytest.mark.parametrize('create', [
    lambda: WorldPos(-1, 0), lambda: WorldPos(0.1, 0),
    lambda: Soldier(1, 2, WorldPos(0, 0)),
    lambda: Soldier(0, Team.A, WorldPos(0, 0)),
    lambda: Squad(1, Team.A, WorldPos(0, 0), [2, 2]),
    lambda: Squad(1, Team.A, WorldPos(0, 0), list(range(2, 8))),
])
def test_invalid_entity(create):
    with pytest.raises(ValueError):
        create()
