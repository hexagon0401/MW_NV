import json
from pathlib import Path
from server.releases import Registry
from test_releases import spec,ready,cmd
import server.canary_watch as watcher


def test_canary_failure_retries_once_then_serialized_rollback(tmp_path,monkeypatch):
    registry=Registry(tmp_path/'releases');candidate=spec();candidate['artifact']['activation']='canary';d=registry.register(candidate)
    registry.observe('test',dict(steps=[dict(id='engine',state='PASS')],evidence_digest=d,connection='online'))
    attempt=registry.command(cmd(d))['attempt_id'];registry.journal(attempt,'APPLIED',old_run={'root':'saved'})
    run=tmp_path/'run';run.mkdir();(run/'state.json').write_text('{}');(registry.root/'active.json').write_text(json.dumps(dict(root=str(run),release_id='test',revision=1)))
    from server import ppo_control
    calls=[];monkeypatch.setattr(ppo_control,'resume_if_needed',lambda *a:calls.append('resume'))
    watcher.monitor(registry,tmp_path,100);watcher.monitor(registry,tmp_path,131);assert calls==['resume']
    watcher.monitor(registry,tmp_path,200);assert registry.pending() is None
    watcher.monitor(registry,tmp_path,312);assert registry.pending()['action']=='rollback'


def test_administrator_pause_is_never_undone_by_canary_recovery(tmp_path):
    registry=Registry(tmp_path/'releases');candidate=spec();candidate['artifact']['activation']='canary';d=registry.register(candidate)
    registry.observe('test',dict(steps=[dict(id='engine',state='PASS')],evidence_digest=d));attempt=registry.command(cmd(d))['attempt_id'];registry.journal(attempt,'APPLIED')
    (registry.root/'active.json').write_text(json.dumps(dict(root=str(tmp_path/'run'),release_id='test',revision=1)))
    control=tmp_path/'data/control';control.mkdir(parents=True);(control/'state.json').write_text('{"desired":"paused"}')
    watcher.monitor(registry,tmp_path,1000);assert registry.pending() is None and not (registry.root/'canary-health.json').exists()
