"""The same permitted mission candidates for local rules, NumPy PPO and bounded LLM HQ."""
from .tactics import TacticalHQ,select,shortlist
from .mission_tactics import candidates,commands
from .hybrid_hq import HybridHQ

class MissionHQ(TacticalHQ):
    def ranked(self,obs):
        items=candidates(obs);self.policy_status='algorithm'
        if self.policy and not self.policy_error:
            try:
                import numpy as np
                from learning.mission_numpy import NumpyPolicy
                from learning.mission_features import vector
                if self.model is None:self.model=NumpyPolicy(self.policy)
                scores=self.model.logits(vector(obs,items))
                if not np.isfinite(scores).all():raise ValueError('nonfinite actor')
                for c in items:c['policy_score']=float(scores[c['id']])
                self.policy_status=self.model.policy_id
            except (OSError,ValueError,KeyError,TypeError):self.policy_error=True
        if self.policy_error:self.policy_status='incompatible_policy_fallback'
        return items
    def observe_and_issue(self,obs):
        selected=select(self.ranked(obs));self.last_decision=dict(source='algorithm',policy=self.policy_status,contract='tactics-3',reasons=[dict(unit=c['command']['unit'],candidate_id=c['id'],reason=c['reason'],score=c['score']) for c in selected]);return commands(obs,selected)

class MissionHybridHQ(HybridHQ):
    def __init__(self,*args,policy=None,**kwargs):super().__init__(*args,policy=policy,**kwargs);self.tactical=MissionHQ(policy)
    def observe_and_issue(self,obs):
        self.offered=shortlist(self.tactical.ranked(obs));self.observation=obs
        try:
            from .teacher import choose
            selected=choose(self,obs,self.offered);self.last_decision=dict(source='llm',model=self.model,policy=self.tactical.policy_status,contract='tactics-3',reasons=[dict(unit=c['command']['unit'],candidate_id=c['id'],reason=c['reason'],score=c['score']) for c in selected]);return commands(obs,selected)
        except (OSError,TimeoutError,ValueError,KeyError,IndexError,TypeError):return self.fallback(obs,'MODEL_OR_CANDIDATE_FAILURE')
