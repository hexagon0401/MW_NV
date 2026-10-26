"""Bounded paired NIM supervision; never blocks or controls a PPO rollout."""
import copy,time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

class AsyncTeacher:
    def __init__(self,querier,buffers,interval=30):
        self.querier=querier;self.buffers=buffers;self.interval=interval
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='nim-pair')
        self.future=None;self.next_request=time.monotonic()+max(0,querier.stats.get('next_request_at',0)-time.time());self.last_worker=querier.stats.get('async_worker');self.closed=False
        self.querier.stats['async_inflight']=False
    def drain(self):
        if self.future is None or not self.future.done():return
        self.future.result();self.future=None
        for row in self.querier.rows:
            learner=self.assignments.get(('A','B')[row[3]])
            if learner in ('PPO1','PPO2'):self.buffers[int(learner[-1])-1].rows.append(row)
        self.querier.rows.clear()
    def offer(self,env,assignments,worker=0,generation=0):
        self.drain();now=time.monotonic()
        if self.closed or self.future is not None or now<max(self.next_request,self.querier.cooldown):
            self.querier.stats['async_skipped']=self.querier.stats.get('async_skipped',0)+1;return False
        observations=copy.deepcopy(getattr(env,'cached_observations',None) or {a:env.raw(a) for a in ('A','B')})
        snapshot=SimpleNamespace(items=copy.deepcopy(env.items),raw=lambda a:observations[a])
        self.assignments=dict(assignments);self.next_request=now+self.interval;self.last_worker=worker
        counts=self.querier.stats.setdefault('worker_attempts',{});counts[str(worker)]=counts.get(str(worker),0)+1
        self.querier.stats.update(next_request_at=time.time()+self.interval,async_worker=worker,source_generation=generation,async_inflight=True)
        def collect():
            try:self.querier.collect(snapshot)
            finally:self.querier.stats['async_inflight']=False
        self.future=self.pool.submit(collect);return True
    def close(self):
        self.closed=True;self.drain()
        # Outstanding remote calls are bounded by the existing timeout; no pending labels
        # are checkpointed or interpreted as PPO experience.
        self.pool.shutdown(wait=False,cancel_futures=True)
