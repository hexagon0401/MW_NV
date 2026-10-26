"""Persistent process-owned engine; only HQ features cross the inference boundary."""
import multiprocessing as mp,os,traceback
from types import SimpleNamespace
from .league_metrics import new_metrics,opportunity,selection
from engine.runtime import Engine
from engine.viewer_export import frame
from server.telemetry import Activity

FIELDS=('agents','items','selected','finished','reserved_supply','initial_costs','history')
def snapshot(env):
    return dict(world=env.engine.world,presentation_events=env.engine.presentation_events,scenario_id=getattr(env,'scenario_id',None),**{k:getattr(env,k) for k in FIELDS})
def restore(env,payload):
    env.engine=Engine(payload['world']);env.engine.presentation_events=payload['presentation_events']
    for k in FIELDS:setattr(env,k,payload[k])
    if payload.get('scenario_id') is not None:env.scenario_id=payload['scenario_id']
    env.cached_observations={a:env.raw(a) for a in ('A','B')};env.cached_tick=env.engine.world.tick
    return env

def make_env(kind):
    if kind=='mission':
        from .mission_env import MissionEnv
        return MissionEnv(decision_seconds=10)
    from .candidate_env import CandidateEnv
    from .training_maps import training_scenario
    return CandidateEnv(scenario_factory=training_scenario,decision_seconds=10)

def packet(env,rewards=None):
    return dict(tick=env.engine.world.tick,ended=not bool(env.agents),finished=dict(env.finished),
                vectors={a:env.vector(a) for a in ('A','B')},masks={a:env.mask(a) for a in ('A','B')},
                heuristic={a:env.heuristic(a) for a in ('A','B')},rewards=rewards or {'A':0.,'B':0.})

def serve(conn,kind):
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
    activity=None;env=make_env(kind);env.reset(0);info=dict(active=False,assignments={},episode_starts={'A':True,'B':True},policy_spans={});metric_tick=None
    while True:
        try:
            op,data=conn.recv()
            if op=='close':
                if activity:activity.close('IDLE')
                return
            if op=='load':
                restore(env,data['environment']);info=data['info'];activity=Activity('training',str(info.get('episode','unknown')),info.get('run_id'),getattr(env,'scenario_id','2'),list(info.get('assignments',{}).values())) if info.get('active') else None
                if activity:activity.update(env.engine.world.tick,state='WAITING',force=True)
                metric_tick=env.engine.world.tick if any(env.selected.values()) else None;conn.send(packet(env))
            elif op=='reset':
                info=data;d=info['descriptor'];env.scenario_id=d.get('scenario_id','2')
                seed=d['seed'] if kind=='mission' else (d['seed']%2000)*4+d['family']
                env.reset(seed,options={'swap':d['swap']});info.update(initial_frame=frame(env.engine.world),metrics=new_metrics(),episode_starts={'A':True,'B':True},policy_spans={a:[info['generation']] for a,l in info['assignments'].items() if l in ('PPO1','PPO2')});metric_tick=None;activity=Activity('training',str(info['episode']),info.get('run_id'),d.get('scenario_id','2'),list(info['assignments'].values()));conn.send(packet(env))
            elif op=='step':
                actions,generation=data;before=env.engine.world.tick
                if metric_tick!=before:
                    for a in ('A','B'):opportunity(info['metrics'],a,env.items[a])
                    metric_tick=before
                for a,action in actions.items():
                    if action!=64 and not env.finished[a]:selection(info['metrics'],a,next(c for c in env.items[a] if c['id']==action),before)
                env.decision_sources={a:l+' 지휘' for a,l in info['assignments'].items()}
                for a,spans in info['policy_spans'].items():
                    if spans[-1]!=generation:spans.append(generation)
                _,rewards,*_=env.step(actions)
                if activity:activity.update(env.engine.world.tick,state='RUNNING' if env.agents else 'COMPLETED')
                conn.send(packet(env,rewards))
            elif op=='mark':
                if activity:activity.update(env.engine.world.tick,state=data if env.agents else 'IDLE',force=True)
                conn.send(True)
            elif op=='teacher':conn.send(SimpleNamespace(cached_observations=env.cached_observations,items=env.items))
            elif op=='snapshot':conn.send(dict(environment=snapshot(env),info=info))
            else:raise ValueError('unknown environment operation')
        except EOFError:return
        except Exception:conn.send(dict(error=traceback.format_exc()));return

class ProcessEnv:
    def __init__(self,kind):
        context=mp.get_context('spawn');self.conn,remote=context.Pipe();self.process=context.Process(target=serve,args=(remote,kind),daemon=True);self.process.start();remote.close();self.pending=False
    def send(self,op,data=None):
        if self.pending:raise RuntimeError('overlapping environment operation')
        self.conn.send((op,data));self.pending=True
    def receive(self):
        value=self.conn.recv();self.pending=False
        if isinstance(value,dict) and 'error' in value:raise RuntimeError(value['error'])
        return value
    def call(self,op,data=None):self.send(op,data);return self.receive()
    def close(self):
        if self.process.is_alive():
            if self.pending:self.receive()
            self.conn.send(('close',None));self.process.join(10)
            if self.process.is_alive():self.process.terminate();self.process.join()
        self.conn.close()
