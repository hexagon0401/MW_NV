"""Task-conditioned environment; potential shaping only at real time boundaries."""
import numpy as np
from gymnasium.spaces import Box
from .candidate_env import CandidateEnv
from .mission_features import vector,OBS_SIZE
from .teacher import TeacherBuffer
from agents.mission_tactics import candidates
from agents.tactics import compatible
from engine.multi_scenario import create

class MissionTeacher(TeacherBuffer):
    observation_size=OBS_SIZE
    encode=staticmethod(vector)
    def sample_rows(self):
        import os
        if os.environ.get('MW_NV_MISSION_TEACHER_BASELINE')=='1':return super().sample_rows()
        from collections import defaultdict
        import random
        buckets=defaultdict(list)
        for i,row in enumerate(self.rows):
            meta=row[4] if len(row)>4 else {};buckets[(meta.get('mode','conquest'),meta.get('stage','unknown'))].append(i)
        if len(self.rows)<32:return []
        picked=[]
        for mode,quota in (('elimination',13),('capture_flag',13),('conquest',6)):
            stages=[list(v) for (m,_),v in sorted(buckets.items()) if m==mode]
            for v in stages:random.shuffle(v)
            while stages and quota:
                for v in stages:
                    if v and quota:picked.append(v.pop());quota-=1
                stages=[v for v in stages if v]
        remaining=list(set(range(len(self.rows)))-set(picked))
        picked+=random.sample(remaining,min(32-len(picked),len(remaining)))
        return [self.rows[i] for i in picked]


class MissionEnv(CandidateEnv):
    def __init__(self,scenario_factory=None,decision_seconds=10,scenario_id='2'):
        self.scenario_id=str(scenario_id)
        super().__init__(scenario_factory or self.create,decision_seconds)
        self.observation_spaces={a:Box(-4,4,(OBS_SIZE,),np.float32) for a in self.possible_agents}
    def create(self,seed,swap=False):return create(seed,swap=swap,scenario_id=self.scenario_id)
    def _round(self):
        self.cached_observations={a:self.raw(a) for a in self.possible_agents};self.cached_tick=self.engine.world.tick
        self.items={a:candidates(self.cached_observations[a]) for a in self.possible_agents};self.selected={a:[] for a in self.possible_agents};self.finished={a:False for a in self.possible_agents};self.reserved_supply={a:0 for a in self.possible_agents}
        if hasattr(self,'teacher_hook') and self.engine.world.tick%150==0 and not getattr(self.engine.world,'ended',False):self.teacher_hook(self)
    def vector(self,a):
        raw=self.cached_observations[a] if getattr(self,'cached_tick',None)==self.engine.world.tick else self.raw(a)
        values=vector(raw,compatible(self.items[a],self.selected[a]));values[16]=len(self.selected[a])/4;values[17]=sum(c.get('supply_cost',0) for c in self.selected[a])/max(1,raw['resources']['supply']);return values
    def command_batch(self,a):
        from agents.mission_tactics import commands
        return commands(self.raw(a),self.selected[a])
    def losses(self):
        w=self.engine.world
        return [sum((w.unit_specs if u.id in w.soldiers else w.vehicle_specs)[u.type_id]['cost'] for u in [*w.soldiers.values(),*w.vehicles.values()] if u.team==t and not u.alive and u.type_id!='AA_SITE')/self.initial_costs[t] for t in (0,1)]
    def initial_value(self,t):
        w=self.engine.world
        return max(1,sum((w.unit_specs if u.id in w.soldiers else w.vehicle_specs)[u.type_id]['cost'] for u in [*w.soldiers.values(),*w.vehicles.values()] if u.team==t and u.type_id!='AA_SITE'))
    def potential(self):
        w=self.engine.world;mode=getattr(w,'mode','conquest')
        if getattr(w,'ended',False):return 0.
        if mode=='conquest':return .1*(w.teams[0].score-w.teams[1].score)/w.scenario['score_limit']
        if mode=='elimination':
            losses=self.losses();return .1*(losses[1]-losses[0])
        values=[0.,0.]
        for owner,f in w.flags.items():
            if f['status']=='carried':
                own=w.bases[1-owner]['return_zone'];cx=(own[0]+own[2])/2;cy=(own[1]+own[3])/2
                full=max(1,np.hypot(f['home'][0]-cx,f['home'][1]-cy));distance=np.hypot(f['x_cm']-cx,f['y_cm']-cy)
                values[1-owner]=.5+.5*max(0,1-distance/full)
            elif f['status']=='home':values[1-owner]=.25*f['progress_ms']/(w.scenario['steal_seconds']*1000)
        return .1*(values[0]-values[1])
    def step(self,actions):
        tick=self.engine.world.tick;before=self.potential();obs,_,done,truncated,infos=super().step(actions);w=self.engine.world
        value=0.
        if w.tick!=tick or not self.agents:
            value=.99**((w.tick-tick)*.2/30)*self.potential()-before
            if getattr(w,'ended',False) and w.winner is not None:value+=1 if w.winner==0 else -1
        return obs,{'A':float(value),'B':float(-value)},done,truncated,infos
