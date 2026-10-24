"""Bounded candidate-ID LLM selection; no model-generated engine commands."""
import json
from .local_hq import LocalHQ
from .tactics import TacticalHQ,shortlist,compatible,commands,CONTRACT


class HybridHQ(LocalHQ):
    def __init__(self,*args,policy=None,**kwargs):
        super().__init__(*args,**kwargs);self.tactical=TacticalHQ(policy)
    def observe_and_issue(self,obs):
        self.offered=shortlist(self.tactical.ranked(obs));self.observation=obs
        compact=dict(team=obs['team'],tick=obs['tick'],scores=obs['scores'],resources=obs['resources'],contract=CONTRACT,
            summary=dict(infantry=sum(u['alive'] for u in obs['units']),vehicles=sum(v['alive'] for v in obs['vehicles']),observed_enemies=len(obs['enemies'])),
            candidates=[{k:c[k] for k in ('id','role','score','reason','command','analysis')}|({'policy_score':c['policy_score']} if 'policy_score' in c else {}) for c in self.offered])
        payload=dict(model=self.model,messages=[dict(role='system',content='Choose up to 4 compatible tactical candidate IDs. Return only JSON {"candidate_ids":[integers]}. Use offered IDs, no invented commands. /no_think'),dict(role='user',content=json.dumps(compact,separators=(',',':')))],temperature=0,max_tokens=256,response_format={'type':'json_object'})
        try:
            response=json.loads(self.transport(payload))
            if set(response)!={'candidate_ids'} or not isinstance(response['candidate_ids'],list) or len(response['candidate_ids'])>4:raise ValueError('candidate envelope')
            selected=[];lookup={c['id']:c for c in self.offered}
            for cid in response['candidate_ids']:
                if type(cid) is not int or cid not in lookup or not compatible([lookup[cid]],selected):raise ValueError('candidate invalid/conflict')
                selected.append(lookup[cid])
            self.last_decision=dict(source='llm',model=self.model,policy=self.tactical.policy_status,contract=CONTRACT,fallback_reason=None,reasons=[dict(unit=c['command']['unit'],candidate_id=c['id'],reason=c['reason'],score=c['score']) for c in selected])
            return commands(obs,selected)
        except (OSError,TimeoutError,ValueError,KeyError,IndexError,TypeError):return self.fallback(obs,'MODEL_OR_CANDIDATE_FAILURE')
    def fallback(self,obs,reason):
        result=self.tactical.observe_and_issue(obs);self.last_decision=dict(self.tactical.last_decision,source='algorithm',model=self.model,fallback_reason=reason);return result
