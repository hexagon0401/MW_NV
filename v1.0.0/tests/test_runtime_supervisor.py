import json
from pathlib import Path
from server.runtime_lease import lease_valid,hourly_backup_due
from server.runtime_supervisor import restart_allowed,blocked
from server.releases import Registry

def test_lease_deadline_boot_and_missing_file(tmp_path):
    root=tmp_path/'data/releases/production/current';root.mkdir(parents=True);folder=tmp_path/'data/runtime';folder.mkdir()
    (folder/'config.json').write_text(json.dumps(dict(root=str(root))))
    assert not lease_valid(root,tmp_path,now=10,boot='one')
    (folder/'lease.json').write_text(json.dumps(dict(root=str(root),boot_id='one',deadline=100)))
    assert lease_valid(root,tmp_path,now=99,boot='one')
    assert not lease_valid(root,tmp_path,now=100,boot='one')
    assert not lease_valid(root,tmp_path,now=20,boot='other')
    assert not lease_valid(tmp_path/'data/releases/production/other',tmp_path,now=20,boot='one')

def test_attempt_budget_and_hourly_archive():
    assert restart_allowed([900,950],1000)
    assert not restart_allowed([900,950,990],1000)
    assert restart_allowed([1,2,3],1000)
    assert hourly_backup_due({},3600)
    assert not hourly_backup_due({'last_full_request_at':3600},7199)
    assert hourly_backup_due({'last_full_request_at':3600},7200)

def test_admin_stop_and_pause_are_not_overridden(tmp_path):
    root=tmp_path/'data/releases/production/current';root.mkdir(parents=True);Registry(tmp_path/'data/releases');control=tmp_path/'data/control';control.mkdir()
    (control/'state.json').write_text('{"desired":"paused"}')
    assert blocked(tmp_path,root)=='administrator_paused'
    (control/'state.json').write_text('{"desired":"running"}');(root/'STOP').write_text('owner')
    assert blocked(tmp_path,root)=='owned_stop_marker'
    (root/'STOP').unlink();(root/'state.json').write_text('{"pause_reason":"evaluation_regression"}')
    assert blocked(tmp_path,root)=='saved_pause_reason'

def test_real_child_identity_stop_and_recovery(tmp_path):
    import os,signal,time
    from server.runtime_supervisor import spawn,alive
    from server.runtime_lease import boot_id
    (tmp_path/'data/runtime').mkdir(parents=True)
    (tmp_path/'fixture_worker.py').write_text('import time\ntime.sleep(60)\n')
    for role in ('learner','publish','control'):
        first=spawn(tmp_path,role,'fixture_worker',['--role',role])
        try:
            for _ in range(20):
                if alive(first,'fixture_worker',['--role',role]):break
                time.sleep(.02)
            assert alive(first,'fixture_worker',['--role',role])
            assert not alive(first,'fixture_worker',['--role','other'])
            assert not alive(dict(first,boot_id='previous-boot'),'fixture_worker',['--role',role])
        finally:os.kill(first['pid'],signal.SIGTERM)
        for _ in range(50):
            if not alive(first,'fixture_worker',['--role',role]):break
            time.sleep(.02)
        assert not alive(first,'fixture_worker',['--role',role])
        second=spawn(tmp_path,role,'fixture_worker',['--role',role])
        try:assert second['pid']!=first['pid']
        finally:os.kill(second['pid'],signal.SIGTERM)

def test_code_archive_roundtrip_is_deterministic_and_blocks_traversal(tmp_path):
    import hashlib,tarfile,io
    from server.runtime_recovery import pack_code,unpack_code
    from server.release_artifacts import fingerprint,FOLDERS
    runtime=tmp_path/'runtime';runtime.mkdir()
    for folder in FOLDERS:(runtime/folder).mkdir()
    (runtime/'engine/rules.py').write_text('VERSION=6\n')
    sha=hashlib.sha256((runtime/'engine/rules.py').read_bytes()).hexdigest()
    (runtime/'artifact-files.json').write_text(json.dumps({'engine/rules.py':sha}))
    archive=tmp_path/'code.tar.gz';one=pack_code(runtime,archive);two=pack_code(runtime,tmp_path/'again.tar.gz');assert one==two
    unpack_code(archive,tmp_path/'restored',one,fingerprint(runtime));assert (tmp_path/'restored/engine/rules.py').read_bytes()==(runtime/'engine/rules.py').read_bytes()
    bad=tmp_path/'bad.tar'
    with tarfile.open(bad,'w') as tar:
        entry=tarfile.TarInfo('../outside');entry.size=1;tar.addfile(entry,io.BytesIO(b'x'))
    import pytest
    with pytest.raises(ValueError,match='path'):unpack_code(bad,tmp_path/'reject',hashlib.sha256(bad.read_bytes()).hexdigest(),'irrelevant')
    assert not (tmp_path/'outside').exists()

def test_recovery_transport_rejects_untrusted_file_names():
    import pytest
    from server.runtime_recovery import validate_transport
    sha='a'*64;proof=dict(release='runtime-code-123',sha256=sha,transport=dict(asset='runtime.tar.gz',sha256=sha,chunks=[dict(name='runtime.tar.gz.part000',size=100,sha256=sha)]))
    validate_transport(proof)
    proof['transport']['chunks'][0]['name']='../../key'
    with pytest.raises(ValueError,match='chunk'):validate_transport(proof)

def test_bootstrap_never_overwrites_existing_unactivated_checkpoint(tmp_path):
    import pytest
    from server.runtime_supervisor import bootstrap
    root=tmp_path/'data/releases/production/current';root.mkdir(parents=True);(root/'current.json').write_text('{"path":"saved"}')
    (tmp_path/'data/releases/active.json').write_text(json.dumps(dict(root=str(root))))
    with pytest.raises(ValueError,match='Apply required'):bootstrap(tmp_path)
    assert (root/'current.json').read_text()=='{"path":"saved"}'

def test_expired_lease_prevents_actual_ppo_update(tmp_path,monkeypatch):
    import torch
    torch.set_num_threads(1)
    from test_adaptive_acceleration import source
    from learning.accelerated_league import run
    import server.runtime_lease as lease
    actor=source(tmp_path);monkeypatch.chdir(tmp_path);(tmp_path/'data').mkdir()
    monkeypatch.delenv('MW_NV_PUBLISH_TRAINING',raising=False);monkeypatch.delenv('MW_NV_CONTROL_ROOT',raising=False)
    monkeypatch.setattr(lease,'lease_valid',lambda *a,**k:False)
    state=run(tmp_path/'run',actor,max_updates=1,teacher_enabled=False,fixed_workers=1,collection_rounds=1)
    assert state['generation']==0 and state['rounds']==0
    assert 'ppo1_last_update' not in state and 'ppo2_last_update' not in state

def test_real_starting_learner_is_not_mistaken_for_a_failed_restart(tmp_path):
    import os,signal,time
    from server.runtime_supervisor import spawn,observed_learner
    (tmp_path/'data/runtime').mkdir(parents=True);(tmp_path/'data/control').mkdir();(tmp_path/'learning').mkdir();(tmp_path/'learning/__init__.py').write_text('')
    (tmp_path/'learning/accelerated_league.py').write_text('import time\ntime.sleep(60)\n')
    root=tmp_path/'data/releases/production/test';root.mkdir(parents=True)
    (tmp_path/'data/control/run.json').write_text('{"pid":0,"process_start":null,"boot_id":"previous"}')
    info=spawn(tmp_path,'fixture-learner','learning.accelerated_league',['--root',str(root)])
    try:
        for _ in range(30):
            if observed_learner(tmp_path,root)==(True,True):break
            time.sleep(.02)
        assert observed_learner(tmp_path,root)==(True,True)
    finally:os.kill(info['pid'],signal.SIGTERM)
