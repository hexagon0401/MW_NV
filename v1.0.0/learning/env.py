"""Two-agent parallel HQ environment. Each action is one squad + one goal."""
import numpy as np
from gymnasium.spaces import Box,Discrete
from pettingzoo import ParallelEnv
from engine.scenario import create_match
from engine.runtime import Engine
from engine.types import Team
from engine.orders import OrderError


class HQEnv(ParallelEnv):
    metadata={'name':'mw_nv_v1','render_modes':[],'is_parallelizable':True}
    possible_agents=['A','B']
    def __init__(self):
        self.agents=[];self.observation_spaces={a:Box(-1,1,(32,),np.float32) for a in self.possible_agents}
        self.action_spaces={a:Discrete(20) for a in self.possible_agents}
    def observation_space(self,agent):return self.observation_spaces[agent]
    def action_space(self,agent):return self.action_spaces[agent]
    def reset(self,seed=None,options=None):
        self.engine=Engine(create_match(0 if seed is None else seed));self.agents=self.possible_agents.copy()
        return self.observations(),{a:{} for a in self.agents}
    def raw(self,agent):return self.engine.observe(self.possible_agents.index(agent))
    def vector(self,agent):
        obs=self.raw(agent);v=np.zeros(32,dtype=np.float32);byid={u['id']:u for u in obs['units']}
        for index,group in enumerate(sorted(obs['squads'],key=lambda g:g['id'])[:4]):
            members=[byid[i] for i in group['member_ids'] if byid[i]['alive']]
            if not members:continue
            p=members[0]['pos'];v[index*5:index*5+5]=[p['x_cm']/25600,p['y_cm']/25600,len(members)/5,sum(u['ammo'] for u in members)/max(1,len(members)*45),1]
        v[20:24]=[obs['scores'][0]/100,obs['scores'][1]/100,obs['resources']['supply']/1000,obs['tick']/15000]
        for i,f in enumerate(f for f in obs['facilities'] if f['kind']=='OBJECTIVE'):
            v[24+i]=0 if f['owner'] is None else 1 if f['owner']==obs['team'] else -1
        return np.clip(v,-1,1)
    def observations(self):return {a:self.vector(a) for a in self.agents}
    def mask(self,agent):
        obs=self.raw(agent);alive={u['id'] for u in obs['units'] if u['alive'] and u['carrier_id'] is None};mask=np.zeros(20,dtype=bool)
        for i,g in enumerate(sorted(obs['squads'],key=lambda g:g['id'])[:4]):
            if alive.intersection(g['member_ids']):mask[i*5:i*5+5]=True
        if not mask.any():mask[4]=True
        return mask
    def command(self,agent,action):
        obs=self.raw(agent);team=obs['team'];groups=sorted(obs['squads'],key=lambda g:g['id']);slot,goal=divmod(int(action),5)
        group=groups[slot];byid={u['id']:u for u in obs['units']};living=[byid[i] for i in group['member_ids'] if byid[i]['alive'] and byid[i]['carrier_id'] is None]
        c=dict(cmd_id=obs['tick']*100+1,team=team,tick=obs['tick'],ttl=750)
        if not living:return c|dict(op=0)
        c['unit']=group['id']
        if goal<3:
            target=sorted((f for f in obs['facilities'] if f['kind']=='OBJECTIVE'),key=lambda f:f['id'])[goal]
            c.update(op=3,target=target['id'])
        elif goal==3:
            target=next(f for f in obs['facilities'] if f['kind']=='HQ' and f['owner']==team)
            if all((u['pos']['x_cm']-target['pos']['x_cm'])**2+(u['pos']['y_cm']-target['pos']['y_cm'])**2<=90000 for u in living):c.update(op=8,target=target['id'])
            else:c.update(op=2,arg0=target['pos']['x_cm']//100,arg1=target['pos']['y_cm']//100)
        else:c['op']=1
        return c
    def step(self,actions):
        if not self.agents:return {},{},{},{},{}
        before=[self.engine.world.teams[t].score for t in Team];infos={a:{} for a in self.agents}
        for a in self.agents:
            action=actions.get(a,4);mask=self.mask(a)
            invalid=not isinstance(action,(int,np.integer)) or isinstance(action,bool) or not 0<=action<20 or not mask[action]
            if invalid:action=int(np.flatnonzero(mask)[0]);infos[a]['invalid_action']=True
            try:self.engine.submit_for(self.possible_agents.index(a),self.command(a,action))
            except OrderError:infos[a]['invalid_action']=True
        self.engine.step(30);ended=getattr(self.engine.world,'ended',False)
        scores=[self.engine.world.teams[t].score for t in Team];delta=(scores[0]-before[0])-(scores[1]-before[1])
        reward={a:(delta if a=='A' else -delta)/100 for a in self.agents}
        obs=self.observations();terminated={a:ended for a in self.agents};truncated={a:False for a in self.agents}
        if ended:self.agents=[]
        return obs,reward,terminated,truncated,infos
