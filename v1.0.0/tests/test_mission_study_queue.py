import importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('study_queue',Path(__file__).resolve().parents[1]/'scripts/mission_teacher_study.py');study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)

def test_study_waits_for_full_hash_verified_diagnostics(tmp_path):
    audit=tmp_path/'audit';audit.mkdir();(audit/'validation-code.json').write_text(json.dumps(dict(sha256=study.fingerprint(tmp_path))))
    p=audit/'engine-audit.json';p.write_text(json.dumps(dict(complete=False,results=[])));assert not study.ready(tmp_path,audit)
    p.write_text(json.dumps(dict(complete=True,results=[dict(scenario_id=mode,replay_hash_verified=True) for mode in ('2','3','4') for _ in range(10)])));assert study.ready(tmp_path,audit)
    (audit/'validation-code.json').write_text('{"sha256":"changed"}');assert not study.ready(tmp_path,audit)
