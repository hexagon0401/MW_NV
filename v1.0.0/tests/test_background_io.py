import json
import pytest
from learning.background_io import latest,archive,process_latest,disk_guard

def test_latest_coalesces_and_failure_preserves_pending(tmp_path,monkeypatch):
    from cloud.supabase_storage import PrivateStorage
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('SUPABASE_URL','https://fixture');monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY','fixture')
    latest(tmp_path,'status',{'round':1});latest(tmp_path,'status',{'round':2})
    def fail(*a):raise OSError('offline')
    monkeypatch.setattr(PrivateStorage,'_request',fail)
    with pytest.raises(OSError):process_latest(tmp_path,'status')
    assert json.loads((tmp_path/'io-jobs/status.json.working').read_text())['round']==2
    latest(tmp_path,'status',{'round':3});seen=[]
    monkeypatch.setattr(PrivateStorage,'_request',lambda *a:seen.append(json.loads(a[-1])))
    assert process_latest(tmp_path,'status') and seen==[{'round':3}]

def test_archive_pins_checkpoint_before_original_pruning(tmp_path):
    checkpoint=tmp_path/'current';checkpoint.mkdir();(checkpoint/'model').write_bytes(b'weights')
    archive(tmp_path,checkpoint,dict(generation=10,completed_games=0),True)
    (checkpoint/'model').unlink()
    jobs=list((tmp_path/'io-jobs/archives').glob('*'));assert len(jobs)==1
    assert (jobs[0]/'checkpoint/model').read_bytes()==b'weights'
    assert json.loads((jobs[0]/'job.json').read_text())['full']


def test_old_runner_cannot_overwrite_newer_published_status(tmp_path,monkeypatch):
    from cloud.supabase_storage import PrivateStorage
    monkeypatch.chdir(tmp_path);monkeypatch.setenv('SUPABASE_URL','https://fixture');monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY','fixture')
    calls=[];monkeypatch.setattr(PrivateStorage,'_request',lambda *a:calls.append(json.loads(a[-1])))
    latest(tmp_path/'new','status',{'updated_at':'2026-10-26T10:00:00+00:00','phase':'learning'})
    assert process_latest(tmp_path/'new','status')
    latest(tmp_path/'old','status',{'updated_at':'2026-10-26T09:00:00+00:00','phase':'stopped'})
    assert process_latest(tmp_path/'old','status')
    assert len(calls)==1 and calls[0]['phase']=='learning'
