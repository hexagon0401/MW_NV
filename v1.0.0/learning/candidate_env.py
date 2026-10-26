"""Sequential four-command decision barrier; no LLM in CPU PPO training."""
import numpy as np
from gymnasium.spaces import Box,Discrete
from pettingzoo import ParallelEnv
from engine.runtime import Engine
from engine.scenario import create_release_match
from engine.orders import OrderError
from agents.tactics import candidates,compatible,commands
from .candidate_policy import vector,OBS_SIZE,ACTIONS


class CandidateEnv(ParallelEnv):
    metadata={'name':'mw_nv_tactics_v1','render_modes':[],'is_parallelizable':True}
    possible_agents=['A','B']
    def __init__(self,scenario_factory=create_release_match,decision_seconds=30):
        self.scenario_factory=scenario_factory;self.decision_seconds=decision_seconds;self.history={}
        self.agents=[];self.observation_spaces={a:Box(-1,1,(OBS_SIZE,),np.float32) for a in self.possible_agents};self.action_spaces={a:Discrete(ACTIONS) for a in self.possible_agents}
    def observation_space(self,agent):return self.observation_spaces[agent]
    def action_space(self,agent):return self.action_spaces[agent]
    def reset(self,seed=None,options=None):
        self.engine=Engine(self.scenario_factory(seed or 0,swap=bool((options or {}).get('swap',False))))
        self.history={};self.agents=self.possible_agents.copy();self.initial_costs=[self.initial_value(t) for t in (0,1)];self._round();return self.observations(),{a:{} for a in self.agents}
    def raw(self,a):
        obs=self.engine.observe(self.possible_agents.index(a));obs['recent_summary']=self.history.get(a,[]);return obs
    def _round(self):
        self.cached_observations={a:self.raw(a) for a in self.possible_agents};self.cached_tick=self.engine.world.tick
        self.items={a:candidates(self.cached_observations[a]) for a in self.possible_agents};self.selected={a:[] for a in self.possible_agents};self.finished={a:False for a in self.possible_agents};self.reserved_supply={a:0 for a in self.possible_agents}
        if hasattr(self,'teacher_hook') and self.engine.world.tick%150==0 and not getattr(self.engine.world,'ended',False):self.teacher_hook(self)
    def vector(self,a):
        raw=self.cached_observations[a] if getattr(self,'cached_tick',None)==self.engine.world.tick else self.raw(a)
        values=vector(raw,compatible(self.items[a],self.selected[a]));values[16]=len(self.selected[a])/4;values[17]=sum(c.get('supply_cost',0) for c in self.selected[a])/2000;return values
    def observations(self):return {a:self.vector(a) for a in self.agents}
    def mask(self,a):
        mask=np.zeros(ACTIONS,dtype=bool);mask[64]=True
        if not self.finished[a]:
            for c in compatible(self.items[a],self.selected[a]):mask[c['id']]=True
        return mask
    def heuristic(self,a):
        available=[c for c in self.items[a] if self.mask(a)[c['id']]]
        return max(available,key=lambda c:(c['score'],-c['id']))['id'] if available else 64
    def command_batch(self,a):return commands(self.raw(a),self.selected[a])
    def step(self,actions):
        if not self.agents:return {},{},{},{},{}
        infos={a:{} for a in self.agents};reward={a:0. for a in self.agents};w=self.engine.world
        for a in self.agents:
            action=actions.get(a,64);mask=self.mask(a)
            if type(action) not in (int,np.int64,np.int32) or not 0<=action<ACTIONS or not mask[action]:action=64;infos[a]['invalid_action']=True
            if self.finished[a]:continue
            if action==64:self.finished[a]=True
            else:
                chosen=next(c for c in self.items[a] if c['id']==action);self.selected[a].append(chosen)
                if len(self.selected[a])==4:self.finished[a]=True
        if all(self.finished.values()):
            before=[w.teams[t].score for t in (0,1)];loss_before=self.losses()
            for a in self.possible_agents:
                batch=self.command_batch(a)
                self.engine.record_presentation('HQ_DECISION',team=self.possible_agents.index(a),commands=batch,metadata=dict(source=getattr(self,'decision_sources',{}).get(a,'정책 선택'),reasons=[dict(unit=c['command']['unit'],reason=c['reason'],score=c['score']) for c in self.selected[a]]))
                for c in batch:
                    try:self.engine.submit_for(self.possible_agents.index(a),c)
                    except OrderError:infos[a]['invalid_action']=True
            self.history={a:self.vector(a)[:7].tolist()+self.history.get(a,[])[:7] for a in self.possible_agents}
            self.engine.step(self.decision_seconds);loss_after=self.losses();delta=(w.teams[0].score-before[0])-(w.teams[1].score-before[1])
            value=.01*delta+.1*((loss_after[1]-loss_before[1])-(loss_after[0]-loss_before[0]))
            if getattr(w,'ended',False) and w.winner is not None:value+=1 if w.winner==0 else -1
            reward={'A':value,'B':-value};self._round()
        ended=getattr(w,'ended',False);obs=self.observations();done={a:ended for a in self.agents};truncated={a:False for a in self.agents}
        if ended:
            for a in self.agents:infos[a]['winner']=None if w.winner is None else int(w.winner)
            self.agents=[]
        return obs,reward,done,truncated,infos
    def losses(self):
        w=self.engine.world
        return [sum((w.unit_specs if u.id in w.soldiers else w.vehicle_specs)[u.type_id]['cost'] for u in [*w.soldiers.values(),*w.vehicles.values()] if u.team==t and not u.alive)/self.initial_costs[t] for t in (0,1)]
    def initial_value(self,t):
        w=self.engine.world
        return max(1,sum((w.unit_specs if u.id in w.soldiers else w.vehicle_specs)[u.type_id]['cost'] for u in [*w.soldiers.values(),*w.vehicles.values()] if u.team==t))
