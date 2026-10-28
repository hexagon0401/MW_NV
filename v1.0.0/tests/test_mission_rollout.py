import json
from pathlib import Path
import learning.mission_rollout as rollout


def setup(tmp,monkeypatch):
    monkeypatch.chdir(tmp);folder=tmp/'docs/multi-mode';folder.mkdir(parents=True);(folder/'validation.json').write_text(json.dumps(dict(static_checks_passed=True,geometry_complete=True,code_sha256='fixed')));(folder/'source-archive.json').write_text('[{"status":"verified"}]');monkeypatch.setattr(rollout,'code_fingerprint',lambda:'fixed');monkeypatch.setattr(rollout,'audit',lambda *a,**k:dict(complete=True,results=[dict(complete=True,replay_hash_verified=True) for _ in range(30)]));legacy=tmp/'legacy';legacy.mkdir();return legacy


def test_retention_failure_never_stops_existing_training(tmp_path,monkeypatch):
    old=setup(tmp_path,monkeypatch);monkeypatch.setattr(rollout,'migration_gate',lambda *a,**k:dict(retained=False,intervals={'1':dict(low=-.5,high=-.2)}));state=rollout.run(tmp_path/'new',old);assert state['reason']=='map2_retention_not_established';assert not (old/'STOP').exists() and not state['mixed_training_started']


def test_validated_candidate_never_stops_or_replaces_operational_learner(tmp_path,monkeypatch):
    old=setup(tmp_path,monkeypatch)
    monkeypatch.setattr(rollout,'migration_gate',lambda *a,**k:dict(retained=True,intervals={'1':dict(low=0,high=0)}))
    monkeypatch.setattr(rollout.subprocess,'run',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('must not launch production')))
    state=rollout.run(tmp_path/'new',old)
    assert state['stage']=='candidate_validated' and not state['mixed_training_started']
    assert not (old/'STOP').exists()
    assert json.loads((tmp_path/'new/validation-gates.json').read_text())['production_apply_required']


def test_authorized_canary_keeps_engine_gates_and_does_not_forge_retention_or_apply(tmp_path,monkeypatch):
    old=setup(tmp_path,monkeypatch);p=tmp_path/'docs/multi-mode/validation.json';certificate=json.loads(p.read_text());certificate['release_profile']='canary';p.write_text(json.dumps(certificate))
    monkeypatch.setattr(rollout,'migration_gate',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('follow-up gate must not block canary')))
    state=rollout.run(tmp_path/'new',old);gate=json.loads((tmp_path/'new/validation-gates.json').read_text())
    assert state['status']=='validated' and gate['engine_games']==30 and gate['production_apply_required']
    assert not gate['retention_verified'] and not gate['performance_verified'] and not (old/'STOP').exists()
