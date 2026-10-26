import json
from pathlib import Path
import learning.mission_rollout as rollout


def setup(tmp,monkeypatch):
    monkeypatch.chdir(tmp);folder=tmp/'docs/multi-mode';folder.mkdir(parents=True);(folder/'validation.json').write_text(json.dumps(dict(static_checks_passed=True,geometry_complete=True,code_sha256='fixed')));(folder/'source-archive.json').write_text('[{"status":"verified"}]');monkeypatch.setattr(rollout,'code_fingerprint',lambda:'fixed');monkeypatch.setattr(rollout,'audit',lambda *a,**k:dict(complete=True,results=[dict(complete=True,replay_hash_verified=True) for _ in range(30)]));legacy=tmp/'legacy';legacy.mkdir();return legacy


def test_retention_failure_never_stops_existing_training(tmp_path,monkeypatch):
    old=setup(tmp_path,monkeypatch);monkeypatch.setattr(rollout,'migration_gate',lambda *a,**k:dict(retained=False,intervals={'1':dict(low=-.5,high=-.2)}));state=rollout.run(tmp_path/'new',old);assert state['reason']=='map2_retention_not_established';assert not (old/'STOP').exists() and not state['mixed_training_started']


def test_archive_failure_cancels_legacy_pause_without_duplicate_worker(tmp_path,monkeypatch):
    old=setup(tmp_path,monkeypatch);monkeypatch.setattr(rollout,'migration_gate',lambda *a,**k:dict(retained=True,intervals={'1':dict(low=0,high=0)}));(old/'runner.pid').write_text('123');(old/'current.json').write_text('{"path":"checkpoint"}');(old/'checkpoint').mkdir();(old/'checkpoint/state.json').write_text('{"generation":70}')
    original=Path.read_bytes;calls=[]
    def read(path):
        if str(path)=='/proc/123/cmdline':
            calls.append(1)
            if len(calls)==2:raise FileNotFoundError()
            return b'python\0-m\0learning.league\0--root\0legacy\0'
        return original(path)
    monkeypatch.setattr(Path,'read_bytes',read)
    import learning.league_archive as archive
    monkeypatch.setattr(archive,'spool',lambda *a,**k:None);monkeypatch.setattr(archive,'publish_pending',lambda *_:dict(status='deferred'))
    def no_duplicate(*a,**k):raise AssertionError('Must not duplicate an existing legacy worker')
    monkeypatch.setattr(rollout.subprocess,'Popen',no_duplicate);state=rollout.run(tmp_path/'new',old)
    assert state['status']=='paused' and state['legacy_pause_cancelled'];assert not (old/'STOP').exists()
