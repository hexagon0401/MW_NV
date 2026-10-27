import uuid,time
import pytest
from server.releases import Registry


def spec(revision=1):return dict(id='test',revision=revision,title='Test',description='Test',targets=['training'],dependencies=[],handler='mixed_training',artifact={'artifact_id':'test'},validation_plan=['engine'],planned=False)
def ready(r):
    digest=r.register(spec());r.observe('test',dict(steps=[dict(id='engine',state='PASS',required=True)],blockers=[],connection='online',evidence_digest=digest));return digest

def cmd(d,action='apply',enabled=None):
    now=time.time()
    return dict(request_id=str(uuid.uuid4()),release_id='test',content_digest=d,action=action,enabled=enabled,actor_id='82876856',created_at=now,expires_at=None if action=='set_auto' else now+600)


def test_ready_requires_current_evidence_and_all_required_checks(tmp_path):
    r=Registry(tmp_path);d=r.register(spec());r.observe('test',dict(steps=[dict(id='engine',state='PASS')],evidence_digest='wrong'))
    assert r.get('test')['status']!='READY'
    with pytest.raises(ValueError):r.command(cmd(d))
    assert ready(r)==d and r.get('test')['status']=='READY'


def test_auto_intent_survives_session_and_registry_restart_but_not_revision(tmp_path):
    r=Registry(tmp_path);d=ready(r);r.command(cmd(d,'set_auto',True));assert Registry(tmp_path).get('test')['auto_apply']
    r.register(spec(2));assert not r.get('test')['auto_apply']
    with pytest.raises(ValueError):r.command(cmd(d))


def test_idempotency_global_single_apply_and_recovery_journal(tmp_path):
    r=Registry(tmp_path);d=ready(r);c=cmd(d);a=r.command(c);assert r.command(c)==a
    with pytest.raises(ValueError):r.command(cmd(d))
    r.journal(a['attempt_id'],'SAVING',snapshot='private')
    assert Registry(tmp_path).pending()['phase']=='SAVING'
    r.journal(a['attempt_id'],'APPLIED');assert r.get('test')['status']=='APPLIED'
    assert 'snapshot' not in str(r.get('test'))


def test_auto_only_when_ready_and_foreign_actor_rejected(tmp_path):
    r=Registry(tmp_path);d=r.register(spec());r.command(cmd(d,'set_auto',True));assert r.auto_request() is None
    ready(r);assert r.auto_request()['status']=='accepted'
    bad=cmd(d);bad['actor_id']='other'
    with pytest.raises(ValueError):r.command(bad)


def test_terminal_events_paginate_without_exposing_journal(tmp_path):
    r=Registry(tmp_path);ready(r)
    with r.db() as c:
        for i in range(250):r.event(c,'test','CHECK_PROGRESS',completed=i)
    rows=r.events('test');assert len(rows)==200 and rows==sorted(rows,key=lambda r:r['seq'])
    older=r.events('test',before=rows[0]['seq']);assert older[-1]['seq']<rows[0]['seq']
    assert r.events('test',after=rows[-1]['seq'])==[]


def test_declared_required_checks_cannot_be_missing_or_made_optional(tmp_path):
    r=Registry(tmp_path);s=spec();s['validation_plan']=['engine','pilot'];d=r.register(s)
    r.observe('test',dict(steps=[dict(id='engine',state='PASS')],evidence_digest=d));assert r.get('test')['status']!='READY'
    r.observe('test',dict(steps=[dict(id='engine',state='PASS'),dict(id='pilot',state='FAIL',required=False)],evidence_digest=d));assert r.get('test')['status']!='READY'


def test_retry_after_request_expiration_keeps_original_ack(tmp_path):
    r=Registry(tmp_path);d=ready(r);payload=cmd(d);result=r.command(payload)
    assert r.command(payload,now=payload['expires_at']+1000)==result


def test_remote_automatic_intent_can_restore_after_local_registry_loss(tmp_path):
    from server.release_service import restore_authorizations
    original=Registry(tmp_path/'old');d=ready(original);payload=cmd(d,'set_auto',True);original.command(payload)
    restored=Registry(tmp_path/'new');ready(restored)
    class Store:
        bucket='private'
        def _request(self,*args):
            import json
            return json.dumps(payload).encode()
    restore_authorizations(restored,Store());assert restored.get('test')['auto_apply']


def test_changed_artifacts_clear_auto_without_erasing_history(tmp_path):
    r=Registry(tmp_path);d=ready(r);r.command(cmd(d,'set_auto',True))
    r.observe('test',dict(steps=[dict(id='engine',state='WAIT')],evidence_digest=None,invalidated=True))
    assert not r.get('test')['auto_apply']
    assert any(e['code']=='AUTO_INVALIDATED' for e in r.events('test'))


def test_agent_bootstrap_does_not_downgrade_registered_future_revision(tmp_path):
    from server.release_service import definitions
    import yaml,json
    root=tmp_path/'registry';registry=Registry(root);base=tmp_path/'base';(base/'config').mkdir(parents=True)
    old=spec();new=spec();new['revision']=2;registry.register(new)
    (base/'config/releases.yaml').write_text(yaml.safe_dump(dict(releases=[old])))
    (root/'definitions').mkdir();path=root/'definitions/test.json';path.write_text(json.dumps(dict(spec=new,paths={})))
    definitions(registry,base)
    assert registry.get('test')['revision']==2 and json.loads(path.read_text())['spec']==new
