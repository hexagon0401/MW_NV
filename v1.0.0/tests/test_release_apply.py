import json
import pytest
from server.releases import Registry
import server.release_apply as module
from test_releases import spec,ready,cmd


def prepared(tmp_path,monkeypatch):
    r=Registry(tmp_path);d=ready(r);(tmp_path/'definitions').mkdir();(tmp_path/'definitions/test.json').write_text(json.dumps(dict(spec=spec(),paths={})))
    monkeypatch.setattr(module,'observe',lambda *a:dict(evidence_digest=d,steps=[dict(id='engine',state='PASS')],blockers=[]))
    return r,d


def test_apply_journal_and_duplicate_request_only_switch_once(tmp_path,monkeypatch):
    r,d=prepared(tmp_path,monkeypatch);calls=[]
    class Handler:
        def __init__(self,*_):pass
        def validate(self):calls.append('validate')
        def prepare(self,j,n):n(old='saved');calls.append('save')
        def switch(self,j,n):assert j['old']=='saved';n(new='installed');calls.append('switch')
        def verify(self,j):assert j['new']=='installed';calls.append('verify')
    payload=cmd(d);r.command(payload);module.execute(r,{'mixed_training':Handler});module.execute(r,{'mixed_training':Handler})
    assert calls==['validate','save','switch','verify'] and r.get('test')['status']=='APPLIED'
    assert r.command(payload)['status']=='accepted'


def test_switch_failure_restores_old_state_and_disables_auto(tmp_path,monkeypatch):
    r,d=prepared(tmp_path,monkeypatch);r.command(cmd(d));calls=[]
    class Handler:
        def __init__(self,*_):pass
        def validate(self):pass
        def prepare(self,j,n):n(old='preserved')
        def switch(self,j,n):raise RuntimeError('private/host/path must not be published')
        def rollback(self,j,n):assert j['old']=='preserved';calls.append('restored')
    module.execute(r,{'mixed_training':Handler});assert calls==['restored']
    assert r.get('test')['status']=='ROLLED_BACK'
    assert 'private/host' not in json.dumps(r.events('test'))


def test_restart_from_verifying_does_not_switch_again(tmp_path,monkeypatch):
    r,d=prepared(tmp_path,monkeypatch);attempt=r.command(cmd(d))['attempt_id'];r.journal(attempt,'VERIFYING',new='installed')
    class Handler:
        def __init__(self,*_):pass
        def verify(self,j):assert j['new']=='installed'
    module.execute(r,{'mixed_training':Handler});assert r.get('test')['status']=='APPLIED'


def test_ready_rechecked_before_actual_execution(tmp_path,monkeypatch):
    r,d=prepared(tmp_path,monkeypatch);r.command(cmd(d));monkeypatch.setattr(module,'observe',lambda *a:dict(evidence_digest='changed',steps=[],blockers=[]))
    class Handler:
        def __init__(self,*_):pass
        def validate(self):raise AssertionError('must not execute')
    module.execute(r,{'mixed_training':Handler});assert r.get('test')['status']=='FAILED'


def test_failed_rollback_keeps_exclusive_recovery_state(tmp_path,monkeypatch):
    r,d=prepared(tmp_path,monkeypatch);r.command(cmd(d))
    class Handler:
        def __init__(self,*_):pass
        def validate(self):pass
        def prepare(self,j,n):n(old='safe')
        def switch(self,j,n):raise RuntimeError()
        def rollback(self,j,n):raise RuntimeError()
    module.execute(r,{'mixed_training':Handler})
    assert r.pending()['phase']=='RECOVERY_REQUIRED'
    with pytest.raises(ValueError):r.command(cmd(d))
