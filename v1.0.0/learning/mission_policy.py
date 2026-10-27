"""Shared-row actor, independent critic, permutation-equivariant masked logits."""
import hashlib
import numpy as np
import torch
from torch import nn
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from .mission_features import CONTRACT,OBS_SIZE,ACTIONS

class CandidateNetwork(nn.Module):
    latent_dim_pi=65
    latent_dim_vf=128
    def __init__(self):
        super().__init__()
        for prefix in ('pi','vf'):
            setattr(self,prefix+'_rows',nn.Sequential(nn.Linear(24,64),nn.Tanh(),nn.Linear(64,64),nn.Tanh()))
            setattr(self,prefix+'_context',nn.Sequential(nn.Linear(64,128),nn.Tanh(),nn.Linear(128,64),nn.Tanh()))
        self.pi_score=nn.Sequential(nn.Linear(256,64),nn.Tanh(),nn.Linear(64,1));self.pi_stop=nn.Sequential(nn.Linear(192,64),nn.Tanh(),nn.Linear(64,1));self.vf_output=nn.Sequential(nn.Linear(192,128),nn.Tanh())
    def encoded(self,features,prefix):
        raw=features[:,64:].reshape(-1,64,24);valid=raw.abs().sum(-1)>0;rows=getattr(self,prefix+'_rows')(raw);context=getattr(self,prefix+'_context')(features[:,:64]);mean=(rows*valid[...,None]).sum(1)/valid.sum(1).clamp(min=1)[:,None];maximum=rows.masked_fill(~valid[...,None],-1e9).max(1).values;maximum=torch.where(valid.any(1)[:,None],maximum,torch.zeros_like(maximum));return rows,torch.cat((context,mean,maximum),-1)
    def forward_actor(self,features):
        rows,global_features=self.encoded(features,'pi');scores=self.pi_score(torch.cat((rows,global_features[:,None,:].expand(-1,64,-1)),-1)).squeeze(-1);return torch.cat((scores,self.pi_stop(global_features)),-1)
    def forward_critic(self,features):return self.vf_output(self.encoded(features,'vf')[1])
    def forward(self,features):return self.forward_actor(features),self.forward_critic(features)

class MissionPolicy(MaskableActorCriticPolicy):
    def _build_mlp_extractor(self):self.mlp_extractor=CandidateNetwork()
    def _build(self,lr_schedule):
        super()._build(lr_schedule);self.action_net=nn.Identity();self.optimizer=self.optimizer_class(self.parameters(),lr=lr_schedule(1),**self.optimizer_kwargs)


def export(model,path):
    weights={k:v.detach().cpu().numpy() for k,v in model.policy.mlp_extractor.state_dict().items() if k.startswith('pi_')}
    np.savez(path,contract=np.array(CONTRACT),rules_version=np.array('combined-arms-6'),**weights)

from .mission_numpy import NumpyPolicy
