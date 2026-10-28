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


def test_dependency_rollback_after_request_prevents_execution(tmp_path,monkeypatch):
    r,d=prepared(tmp_path,monkeypatch)
    # A dependency can be restored after the request and before worker execution.
    candidate=spec();candidate['revision']=2;candidate['dependencies']=[dict(id='base',revision=1)]
    base=dict(spec(),id='base');r.register(base)
    with r.db() as c:c.execute("UPDATE releases SET state=? WHERE id='base'",(json.dumps(dict(status='APPLIED')),))
    d=r.register(candidate);r.observe('test',dict(evidence_digest=d,steps=[dict(id='engine',state='PASS')],blockers=[]))
    (tmp_path/'definitions/test.json').write_text(json.dumps(dict(spec=candidate,paths={})))
    r.command(cmd(d))
    with r.db() as c:c.execute("UPDATE releases SET state=? WHERE id='base'",(json.dumps(dict(status='ROLLED_BACK')),))
    class Handler:
        def __init__(self,*_):pass
        def validate(self):raise AssertionError('dependent release must not execute')
    module.execute(r,{'mixed_training':Handler});assert r.get('test')['status']=='FAILED'


def test_mixed_prepare_uses_registered_runtime_without_proc_cwd(tmp_path,monkeypatch):
    import server.release_handlers as handlers
    from types import SimpleNamespace
    base=tmp_path;registry=SimpleNamespace(root=base/'data/releases');registry.root.mkdir(parents=True)
    root=base/'data/legacy';root.mkdir();runtime=registry.root/'artifacts/frozen';runtime.mkdir(parents=True)
    control=base/'data/control';control.mkdir();(control/'run.json').write_text(json.dumps(dict(root=str(root),source=str(base/'source.npz'),kind='legacy')))
    (registry.root/'legacy-runtime.json').write_text(json.dumps(dict(root=str(root),runtime=str(runtime))))
    (root/'state.json').write_text(json.dumps(dict(rules_version='old',contract='tactics-2',generation=42)))
    monkeypatch.setattr(handlers,'BASE',base);monkeypatch.setattr(handlers,'stop_run',lambda *a:None);monkeypatch.setattr(handlers,'archive_exact',lambda *a:{'verified':True});monkeypatch.setattr(handlers,'exact_recovery',lambda *a:{'verified':True})
    handler=handlers.MixedTraining(dict(spec=dict(id='mixed',revision=1),paths=dict(legacy=str(root),pilot=str(base/'pilot'))),registry)
    journal={};handler.prepare(journal,lambda **v:journal.update(v))
    assert journal['old_run']['cwd']==str(runtime) and journal['old_version']['generation']==42


def test_canary_source_requires_explicit_canary_and_verified_recovery(tmp_path,monkeypatch):
    import server.release_handlers as handlers
    import server.release_artifacts as artifacts
    from types import SimpleNamespace
    root=tmp_path/'source';root.mkdir();(root/'state.json').write_text(json.dumps(dict(generation=0,canary=True,completed_games=0)))
    monkeypatch.setattr(artifacts,'verify',lambda *a:True);monkeypatch.setattr(handlers,'exact_recovery',lambda *a:{'verified':True})
    h=handlers.MixedTraining(dict(spec=dict(artifact=dict(activation='canary',runtime_digest='pinned')),paths=dict(runtime='frozen',pilot=str(root))),SimpleNamespace())
    h.validate()
    (root/'state.json').write_text(json.dumps(dict(generation=0,completed_games=0)))
    with pytest.raises(ValueError,match='canary source'):h.validate()


def test_pages_artifact_requires_frozen_worker_and_rejects_tampering(tmp_path):
    import hashlib
    from server.release_handlers import PagesSite,digest_files
    artifact=tmp_path/'artifact';dist=artifact/'viewer/dist';dist.mkdir(parents=True)
    (dist/'release-marker.json').write_text('{}');(dist/'_worker.js').write_text('export default {}')
    manifest={str(p.relative_to(artifact)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dist.iterdir()}
    (artifact/'files.json').write_text(json.dumps(manifest))
    h=PagesSite(dict(spec=dict(artifact=dict(sha256=digest_files(manifest))),paths=dict(artifact=str(artifact))),None);h.validate()
    (dist/'_worker.js').write_text('changed')
    with pytest.raises(ValueError,match='changed'):h.validate()
