import json
from collections import Counter
import pytest
from learning.mission_schedule import rotation_descriptor

def test_rotation_boundaries_and_resume():
    for n,mode in [(0,'3'),(9,'3'),(10,'4'),(19,'4'),(20,'2'),(29,'2'),(30,'3')]:
        assert rotation_descriptor(18+n,18)['scenario_id']==mode
        saved=json.loads(json.dumps({'completed':18+n,'origin':18}))
        assert rotation_descriptor(saved['completed'],saved['origin'])==rotation_descriptor(18+n,18)
    with pytest.raises(ValueError):rotation_descriptor(17,18)

def test_rotation_long_run_roles_and_modes():
    rows=[rotation_descriptor(i) for i in range(480)]
    assert Counter(r['scenario_id'] for r in rows)=={'2':160,'3':160,'4':160}
    for start in range(0,480,10):assert len({r['scenario_id'] for r in rows[start:start+10]})==1
    # Preserve the existing role schedule instead of resetting it every ten games.
    assert Counter(r['kind'] for r in rows)=={'duel':240,'past':120,'algorithm':120}
