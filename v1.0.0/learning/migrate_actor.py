"""Explicit rules2 -> rules3 actor transfer. Never resumes critic/optimizer/experience."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import torch
from .candidate_train import TrainingEnv
from .candidate_policy import export,CandidatePolicy
from .teacher import TeacherPPO
from engine.version import RULES_VERSION


def migrate(source,output):
    source=Path(source);output=Path(output)
    if output.with_suffix('.zip').exists():raise ValueError('migration destination exists')
    with np.load(source,allow_pickle=False) as data:
        if str(data['contract'].item())!='tactics-1' or str(data['rules_version'].item())!='combined-arms-2' or RULES_VERSION not in ('combined-arms-3','combined-arms-4'):raise ValueError('explicit migration requires rules2 actor and rules3 target')
        weights={k:data[k].copy() for k in ('w0','b0','w1','b1','wo','bo')}
    expected={'w0':(128,1056),'b0':(128,),'w1':(128,128),'b1':(128,),'wo':(65,128),'bo':(65,)}
    if any(weights[k].shape!=shape or not np.isfinite(weights[k]).all() for k,shape in expected.items()):raise ValueError('invalid actor weights')
    torch.set_num_threads(2)
    model=TeacherPPO('MlpPolicy',TrainingEnv(stats=None),n_steps=64,batch_size=32,n_epochs=2,policy_kwargs={'net_arch':{'pi':[128,128],'vf':[128,128]}},seed=0,device='cpu',verbose=0)
    state=model.policy.state_dict()
    for key,prefix in [('w0','mlp_extractor.policy_net.0.weight'),('b0','mlp_extractor.policy_net.0.bias'),('w1','mlp_extractor.policy_net.2.weight'),('b1','mlp_extractor.policy_net.2.bias'),('wo','action_net.weight'),('bo','action_net.bias')]:state[prefix]=torch.tensor(weights[key])
    model.policy.load_state_dict(state)
    assert model.num_timesteps==0 and not model.policy.optimizer.state
    output.parent.mkdir(parents=True,exist_ok=True);model.save(output);export(model,output.with_suffix('.npz'))
    policy=CandidatePolicy(output.with_suffix('.npz'));obs=np.zeros(1056,dtype=np.float32)
    mask=np.ones(65,dtype=bool);assert int(model.predict(obs,deterministic=True,action_masks=mask)[0])==policy.predict(obs,mask)
    output.with_suffix('.json').write_text(json.dumps(dict(source_rules='combined-arms-2',target_rules=RULES_VERSION,contract=__import__('agents.tactics',fromlist=['CONTRACT']).CONTRACT,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),policy_id=policy.policy_id,actor_only=True,critic='fresh',optimizer='fresh',policy_steps=0,map_id='river-districts',map_version='2'),indent=2)+'\n')
    return model

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',default='data/self-play-v3/seed');a=p.parse_args();migrate(a.source,a.output);print('Actor transfer verified; fresh critic/optimizer/step counter')
