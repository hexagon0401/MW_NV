from engine.replay import RecordingEngine,replay
from engine.scenario import create_release_match
from learning.validation_progress import CaseProgress,replay as observed
import json


def test_validation_observer_preserves_replay_and_emits_actual_journal_progress(tmp_path):
    e=RecordingEngine(create_release_match(4));e.step(.4);doc=e.document()
    with CaseProgress(tmp_path,'2',4,False,None) as p:
        p.case_tick(e.world.tick);result=observed(doc,p)
        assert result.checksum()==replay(doc).checksum()
    d=json.loads((tmp_path/'audit-current.json').read_text());assert d['state']=='COMPLETED' and d['phase']=='replay'
    assert d['journal_completed']==d['journal_total']==len(doc['journal'])
