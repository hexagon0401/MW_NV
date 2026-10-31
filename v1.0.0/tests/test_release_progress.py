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


def test_release_read_model_keeps_missing_evidence_unknown_and_paths_private(tmp_path):
    from server.release_observations import mixed
    root=tmp_path/'validation';root.mkdir();(root/'rollout-status.json').write_text('{"stage":"engine_audit","status":"running"}')
    (root/'engine-audit.json').write_text(json.dumps({'results':[dict(scenario_id='3',complete=True,replay_hash_verified=True) for _ in range(10)]}))
    (root/'audit-current.json').write_text(json.dumps(dict(phase='replay',case='4:1:1',state='RUNNING',sim_seconds=900,journal_completed=10,journal_total=100,private_path='/secret/host')))
    d=mixed(dict(artifact={}),dict(validation=str(root),pilot=str(tmp_path/'pilot'),activity=str(tmp_path/'activity')),'a'*64)
    assert next(x for x in d['steps'] if x['id']=='engine-3')['state']=='PASS'
    assert next(x for x in d['steps'] if x['id']=='pilot')['state']=='WAIT'
    assert next(x for x in d['steps'] if x['id']=='evaluation')['state']=='WAIT'
    assert d['evidence_digest'] is None and '/secret' not in json.dumps(d)
