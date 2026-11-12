import threading,time
from types import SimpleNamespace
from learning.async_teacher import AsyncTeacher
from learning.teacher import TeacherBuffer

def test_nonblocking_frozen_pair_routes_original_learner(tmp_path):
    started=threading.Event();release=threading.Event()
    q=TeacherBuffer();buffers=[TeacherBuffer(),TeacherBuffer()]
    def collect(env):
        started.set();assert release.wait(2)
        assert env.raw('A')['x']==1 and env.items['A']==[1]
        q.rows.extend([('x','m',0,0),('y','n',1,1)])
    q.collect=collect
    env=SimpleNamespace(cached_observations={'A':{'x':1},'B':{'x':2}},items={'A':[1],'B':[2]})
    a=AsyncTeacher(q,buffers,budget_root=tmp_path);assert a.offer(env,{'A':'PPO1','B':'PPO2'})
    assert started.wait(1);env.cached_observations['A']['x']=99;env.items['A'].append(99)
    assert not a.offer(env,{'A':'PPO2','B':'PPO1'})
    assert not buffers[0].rows
    release.set();a.future.result(timeout=2);a.drain()
    assert list(buffers[0].rows)==[('x','m',0,0)] and list(buffers[1].rows)==[('y','n',1,1)]
    assert not a.offer(env,{'A':'PPO1','B':'PPO2'})
    a.close()

def test_admission_budget_survives_restart():
    q=TeacherBuffer();q.stats.update(next_request_at=time.time()+30,async_inflight=True,async_worker=2)
    a=AsyncTeacher(q,[TeacherBuffer(),TeacherBuffer()]);assert a.next_request>time.monotonic()+28 and a.last_worker==2
    assert not q.stats['async_inflight'];a.close()
