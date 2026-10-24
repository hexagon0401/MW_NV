"""Local OpenAI-compatible protocol; only engine-validated opcodes escape."""
import json
from urllib.request import Request,urlopen
from urllib.parse import urlparse
from .rule_hq import RuleHQ
from engine.orders import parse_command,validate,OrderError
from engine.types import Team


class LocalHQ:
    def __init__(self,base_url='http://127.0.0.1:8080/v1',model='local',timeout=60,transport=None):
        url=urlparse(base_url)
        if url.scheme!='http' or url.hostname not in ('localhost','127.0.0.1','::1') or url.username or url.password:
            raise ValueError('local HTTP endpoint required')
        self.base_url=base_url.rstrip('/');self.model=model;self.timeout=timeout
        self.transport=transport or self._request;self.last_decision={}

    def _request(self,payload):
        req=Request(self.base_url+'/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=self.timeout) as response:
            body=response.read(65537)
        if len(body)>65536:raise ValueError('response too large')
        return json.loads(body)['choices'][0]['message']['content']

    def observe_and_issue(self,obs):
        compact=dict(team=obs['team'],tick=obs['tick'],resources=obs['resources'],facilities=obs['facilities'],squads=obs['squads'],
                     units=[{k:u[k] for k in ('id','type_id','pos','hp','ammo','alive','carrier_id')} for u in obs['units']],
                     vehicles=obs['vehicles'],enemies=obs['enemies'])
        prompt='Do not think. /no_think. Return JSON {"commands":[...]}, maximum 4 commands. Each command has integer op, unit, arg0, arg1, target as needed. Opcodes: 0 WAIT,1 HOLD,2 MOVE(x/y metres),3 CAPTURE(target objective),4 DEFEND,5 EMBARK(target carrier),6 DISEMBARK,7 TRANSPORT,8 RESUPPLY,9 HEAL,10 RETREAT,11 PURCHASE(arg0 type 0..9 INF/REC/SUP/MED/ENG/LUV/APC/IFV/HEL/TRK, target owned HQ),12 CANCEL. Use only own units. No shell, prose, or extra fields.'
        payload=dict(model=self.model,messages=[dict(role='system',content=prompt),dict(role='user',content=json.dumps(compact,separators=(',',':')))],temperature=0,max_tokens=512,response_format={'type':'json_object'})
        try:
            content=self.transport(payload)
            value=json.loads(content)
            if not isinstance(value,dict) or set(value)!={'commands'} or not isinstance(value['commands'],list) or len(value['commands'])>4:
                raise ValueError('command envelope')
            commands=[]
            for index,c in enumerate(value['commands']):
                if not isinstance(c,dict) or set(c)-{'op','unit','arg0','arg1','target'}:
                    raise ValueError('command fields')
                raw=c | dict(cmd_id=obs['tick']*100+index+1,team=obs['team'],tick=obs['tick'],ttl=750)
                parse_command(raw);commands.append(raw)
            self.last_decision=dict(source='llm',model=self.model,fallback_reason=None)
            return commands
        except (OSError,TimeoutError,ValueError,KeyError,IndexError,TypeError):
            return self.fallback(obs,'MODEL_OR_SCHEMA_FAILURE')

    def fallback(self,obs,reason):
        self.last_decision=dict(source='rules',model=self.model,fallback_reason=reason)
        return RuleHQ().observe_and_issue(obs)


def issue_hq_round(engine,policies):
    """Decision barrier: no simulation step until both snapshots have decisions."""
    snapshots={t:engine.observe(t) for t in Team};batches={}
    for team in Team:
        policy=policies[team];commands=policy.observe_and_issue(snapshots[team])
        try:
            if len(commands)>4:raise OrderError('TOO_MANY_COMMANDS')
            for command in commands:
                c=validate(engine.world,command)
                if c.team!=team:raise OrderError('FOREIGN_TEAM')
        except OrderError:
            commands=policy.fallback(snapshots[team],'INVALID_GAME_COMMAND')
        batches[team]=commands
    for team,commands in batches.items():
        policy=policies[team]
        engine.record_event('HQ_DECISION',team=int(team),metadata=policy.last_decision,commands=commands)
        for c in commands:engine.submit_for(team,c)
    return batches
