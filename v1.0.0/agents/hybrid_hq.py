"""Bounded candidate-ID LLM selection; no model-generated engine commands."""
import json
from .local_hq import LocalHQ
from .tactics import TacticalHQ,shortlist,compatible,commands,CONTRACT


class HybridHQ(LocalHQ):
    def __init__(self,*args,policy=None,**kwargs):
        super().__init__(*args,**kwargs);self.tactical=TacticalHQ(policy)
    def observe_and_issue(self,obs):
        self.offered=shortlist(self.tactical.ranked(obs));self.observation=obs
        try:
            from .teacher import choose
            selected=choose(self,obs,self.offered)
            self.last_decision=dict(source='llm',model=self.model,policy=self.tactical.policy_status,contract=CONTRACT,fallback_reason=None,reasons=[dict(unit=c['command']['unit'],candidate_id=c['id'],reason=c['reason'],score=c['score']) for c in selected])
            return commands(obs,selected)
        except (OSError,TimeoutError,ValueError,KeyError,IndexError,TypeError):return self.fallback(obs,'MODEL_OR_CANDIDATE_FAILURE')
    def fallback(self,obs,reason):
        result=self.tactical.observe_and_issue(obs);self.last_decision=dict(self.tactical.last_decision,source='algorithm',model=self.model,fallback_reason=reason);return result
