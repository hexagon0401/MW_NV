from urllib.error import HTTPError,URLError
import pytest
from learning.teacher import TeacherBuffer
from learning.candidate_env import CandidateEnv

@pytest.mark.parametrize('error',[TimeoutError(),URLError('offline'),HTTPError('https://fixture',503,'unavailable',{},None)])
def test_network_backoff_preserves_pair_and_recovers(monkeypatch,error):
    env=CandidateEnv();env.reset(0);before=env.engine.world.checksum()
    now=[100.];monkeypatch.setattr('learning.teacher.time.monotonic',lambda:now[0])
    def fail(*args):raise error
    monkeypatch.setattr('learning.teacher.choose',fail)
    b=TeacherBuffer();clients=[object(),object()]
    for delay in [60,120,240,300,300]:
        b.collect(env,clients);assert b.cooldown==now[0]+delay
        assert not b.rows
        requests=b.stats['requests'];b.collect(env,clients)
        assert b.stats['requests']==requests
        now[0]+=delay
    monkeypatch.setattr('learning.teacher.choose',lambda *args:[])
    b.collect(env,clients)
    assert b.stats['paired']==1 and len(b.rows)==2
    assert b.stats['consecutive_network_failures']==0 and b.stats['last_error'] is None
    assert env.engine.world.checksum()==before
