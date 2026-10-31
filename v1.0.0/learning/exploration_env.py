"""Opt-in successor environment. Production requires completed tactics-4 pilot."""
from gymnasium.spaces import Box
import numpy as np
from .mission_env import MissionEnv,MissionTeacher
from .exploration_features import vector,OBS_SIZE
from .decision_inputs import encode
from agents.exploration_routes import candidates
from agents.tactics import compatible

class ExplorationTeacher(MissionTeacher):
    observation_size=OBS_SIZE
    encode=staticmethod(vector)


class ExplorationEnv(MissionEnv):
    contract='tactics-5'
    def __init__(self,scenario_factory=None,decision_seconds=10,scenario_id='2'):
        super().__init__(scenario_factory,decision_seconds,scenario_id)
        self.observation_spaces={a:Box(-4,4,(OBS_SIZE,),np.float32) for a in self.possible_agents}
    def create(self,seed,swap=False):
        from .scenario_variants import create
        return create(seed,swap,self.scenario_id)
    def raw(self,a):
        obs=super().raw(a)
        obs['recent_summary']=getattr(self,'summary_history',{}).get(a,[])
        return obs
    def _round(self):
        self.history_tick=getattr(self,'history_tick',-1)
        tick=self.engine.world.tick
        if tick==0:self.summary_history={};self.history_tick=-1
        if tick!=self.history_tick:
            for a in self.possible_agents:
                o=super().raw(a);units=[u for u in o['units'] if u['alive']];vs=[u for u in o['vehicles'] if u['alive']];limits=o['mission']['limits'];spec=o['catalog']['units']
                current=[len(units)/limits['infantry_limit'],len(vs)/limits['vehicle_limit'],sum(u['hp']/spec[u['type_id']]['hp'] for u in units)/max(1,len(units)),sum(u['ammo']/max(1,spec[u['type_id']]['ammo']) for u in units)/max(1,len(units)),len(o['enemies'])/(limits['infantry_limit']+limits['vehicle_limit']),o['resources']['supply']/max(1,limits['supply']),o['scores'][o['team']]/max(1,limits.get('score_limit',1))]
                # History describes previous physical boundaries, not prefix selections.
                previous=getattr(self,'current_summaries',{}).get(a,[])
                self.summary_history[a]=(previous+self.summary_history.get(a,[])[:7])[:14] if tick else []
                if not hasattr(self,'current_summaries') or tick==0 and a=='A':self.current_summaries={}
                self.current_summaries[a]=current
            self.history_tick=tick
        self.cached_observations={a:self.raw(a) for a in self.possible_agents};self.cached_tick=tick
        self.items={a:candidates(self.cached_observations[a]) for a in self.possible_agents};self.selected={a:[] for a in self.possible_agents};self.finished={a:False for a in self.possible_agents};self.reserved_supply={a:0 for a in self.possible_agents}
    def vector(self,a):
        return encode(self.cached_observations[a],compatible(self.items[a],self.selected[a]),self.selected[a],mission=True,contract=self.contract)
