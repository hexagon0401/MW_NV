import json
import pytest
from engine.replay import RecordingEngine,replay,decode
from engine.scenario import create_match
from agents.local_hq import LocalHQ,issue_hq_round
from engine.types import Team


def test_checkpoint_and_command_replay_reproduce_final_hash_without_model():
    e=RecordingEngine(create_match(4))
    policies={t:LocalHQ(transport=lambda _:'bad') for t in Team}
    issue_hq_round(e,policies);e.step(30)
    issue_hq_round(e,policies);e.step(30)
    doc=json.loads(json.dumps(e.document()))
    assert replay(doc).checksum()==e.world.checksum()
    doc['checksum']='tampered'
    with pytest.raises(ValueError,match='checksum'):replay(doc)


def test_checkpoint_refuses_unregistered_classes():
    with pytest.raises(KeyError):decode({'class':'os.system','attrs':{}})
