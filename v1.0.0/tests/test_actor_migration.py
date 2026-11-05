import numpy as np
import pytest
from learning.migrate_actor import migrate
from learning.candidate_policy import CandidatePolicy


def test_explicit_actor_transfer_preserves_actor_and_resets_learning_state(tmp_path):
    weights=dict(w0=np.ones((128,1056),np.float32)*.001,b0=np.zeros(128,np.float32),w1=np.eye(128,dtype=np.float32),b1=np.zeros(128,np.float32),wo=np.ones((65,128),np.float32)*.002,bo=np.arange(65,dtype=np.float32)*.001)
    src=tmp_path/'old.npz';np.savez(src,contract='tactics-1',rules_version='combined-arms-2',**weights)
    with pytest.raises(ValueError):CandidatePolicy(src)
    model=migrate(src,tmp_path/'seed');p=CandidatePolicy(tmp_path/'seed.npz')
    assert all(np.array_equal(p.weights[k],v) for k,v in weights.items())
    assert model.num_timesteps==0 and not model.policy.optimizer.state
    with pytest.raises(ValueError):migrate(src,tmp_path/'seed')


def test_reporter_stopped_state_does_not_duplicate_status_keyword(tmp_path,monkeypatch):
    from learning.training_status import Reporter
    import json
    monkeypatch.chdir(tmp_path);(tmp_path/'data').mkdir()
    reporter=Reporter(tmp_path,0);reporter({'status':'stopped','phase':'stopped'},force=True)
    assert json.loads((tmp_path/'training-status.json').read_text())['status']=='stopped'
