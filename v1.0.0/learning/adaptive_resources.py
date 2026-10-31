"""Conservative cgroup-aware worker hill-climbing, measured at update boundaries."""
import math,os,time
from pathlib import Path

def resources():
    base=Path('/sys/fs/cgroup');affinity=len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else os.cpu_count() or 1
    try:
        quota,period=(base/'cpu.max').read_text().split();cpus=affinity if quota=='max' else max(1,math.floor(int(quota)/int(period)))
    except (OSError,ValueError):cpus=affinity
    try:
        limit=(base/'memory.max').read_text().strip();free=1-float((base/'memory.current').read_text())/int(limit) if limit!='max' else 1.
    except (OSError,ValueError):free=1.
    try:pressure=float(dict(x.split('=') for x in (base/'cpu.pressure').read_text().splitlines()[0].split()[1:])['avg10'])
    except (OSError,ValueError,KeyError):pressure=0.
    return dict(cpu_budget=min(4,cpus,affinity),memory_free_fraction=free,cpu_pressure=pressure)

class Adaptive:
    def __init__(self,now=None):
        self.workers=1;self.since=time.monotonic() if now is None else now;self.sim=0.;self.blocks=0;self.baseline=None;self.trial=False;self.next_trial=self.since+120;self.pressure_since=None;self.reason='warmup'
    def resume_measurement(self,now=None):
        """Exclude initialization/frozen evaluation from rollout throughput trials."""
        self.since=time.monotonic() if now is None else now
        self.sim=0.;self.blocks=0;self.baseline=None;self.trial=False
        self.next_trial=self.since+120;self.pressure_since=None;self.reason='learning_warmup'
    def observe(self,seconds,resource=None,now=None,reserved=0):
        now=time.monotonic() if now is None else now;r=resource or resources();cap=max(1,min(3,r['cpu_budget']-1-reserved))
        self.sim+=seconds;self.blocks+=1
        pressure=r['memory_free_fraction']<.2 or r['cpu_pressure']>10
        self.pressure_since=(self.pressure_since if self.pressure_since is not None else now) if pressure else None
        elapsed=now-self.since;rate=self.sim/max(.001,elapsed)
        reason=None
        if self.workers>cap:self.workers=cap;reason='cpu_quota'
        elif self.pressure_since is not None and now-self.pressure_since>=30 and self.workers>1:self.workers-=1;reason='resource_pressure'
        elif elapsed>=60 and self.blocks>=2:
            if self.trial:
                if rate<self.baseline*1.05:self.workers=max(1,self.workers-1);reason='trial_no_gain'
                else:reason='trial_accepted'
                self.trial=False;self.baseline=rate
            elif self.baseline and rate<self.baseline*.95 and self.workers>1:
                self.workers-=1;reason='throughput_regression';self.baseline=None
            elif now>=self.next_trial and self.workers<cap and not pressure:
                self.baseline=rate;self.workers+=1;self.trial=True;reason='trial_increase'
            else:self.baseline=rate;reason='steady'
        if reason:
            self.reason=reason;self.since=now;self.sim=0.;self.blocks=0
            if reason!='steady':self.next_trial=now+120
        return dict(workers=self.workers,cpu_budget=r['cpu_budget'],reason=self.reason,resource=r)


def release_reservation():
    import json
    from server.telemetry import process_start
    try:
        r=json.loads(Path('data/releases/reservation.json').read_text())
        if process_start(r['pid'])==r['start'] and time.time()-r['updated_at']<90:return min(2,max(0,int(r['cores'])))
    except (OSError,ValueError,KeyError):pass
    return 0
