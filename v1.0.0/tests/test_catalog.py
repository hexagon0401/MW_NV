import pytest
import yaml
from engine.catalog import load_units,make_soldier
from engine.types import Team,WorldPos


def test_five_exact_unit_profiles():
    specs=load_units()
    assert [(specs[t]['hp'],specs[t]['speed_mps'],specs[t]['detection_m']) for t in ('INF','REC','SUP','MED','ENG')] == [(100,1.6,36),(80,1.9,60),(110,1.3,32),(80,1.6,30),(90,1.4,30)]
    for t in ('MED','ENG'):
        assert specs[t]['attack'] is None
        assert make_soldier(1,Team.A,WorldPos(0,0),t).ammo == 0
    assert make_soldier(1,Team.A,WorldPos(0,0),'MED').heal_pool == 80


def test_invalid_profile_rejected(tmp_path):
    data=load_units();data['INF']['speed_mps']=-1
    path=tmp_path/'units.yaml';path.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError,match='speed_mps'):
        load_units(path)
