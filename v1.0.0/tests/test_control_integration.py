import json
from pathlib import Path
import torch
from test_adaptive_acceleration import source
from learning.accelerated_league import run
from learning.process_env import ProcessEnv,make_env
from learning.league_policy import initialize
from learning.league_state import save
from learning.teacher import TeacherBuffer
from learning.candidate_policy import export
from learning.league_metrics import new_metrics
from engine.viewer_export import frame

def test_ppo_pause_finishes_checkpoint_and_due_evaluation_still_runs(tmp_path,monkeypatch):
    import learning.league_evaluate as evaluation
    torch.set_num_threads(1);actor=source(tmp_path);monkeypatch.chdir(tmp_path);(tmp_path/'data').mkdir();monkeypatch.delenv('MW_NV_PUBLISH_TRAINING',raising=False)
    control=tmp_path/'control';monkeypatch.setenv('MW_NV_CONTROL_ROOT',str(control));root=tmp_path/'run';root.mkdir();(root/'baseline').mkdir()
    env=make_env('legacy');env.reset(0);env.engine.world.teams[0].score=100
    models=[initialize(actor,1),initialize(actor,2)]
    state=dict(schema=1,run='pause-fixture',rules_version='combined-arms-4',catalog_version='combined-arms-2',contract='tactics-2',map_id='river-districts',map_version='2',generation=0,completed_games=49,episode=49,active=True,rounds=0,last_policy_archive=49,last_full_archive=49,last_evaluation=0,assignments={'A':'PPO1','B':'PPO2'},descriptor=dict(kind='duel',team='A',learner=0,swap=False,seed=0,family=0),fixed_opponent=None,initial_frame=frame(env.engine.world),metrics=new_metrics(),episode_starts={'A':True,'B':True},policy_spans={'A':[0],'B':[0]})
    save(root,models,env,[TeacherBuffer(),TeacherBuffer()],TeacherBuffer(),[torch.Generator(),torch.Generator()],state)
    for i,m in enumerate(models):export(m,root/'baseline'/f'ppo{i+1}.npz')
    receive=ProcessEnv.receive;paused=[False];evaluations=[]
    def received(self):
        data=receive(self)
        if isinstance(data,dict) and data.get('tick',0)>0 and not paused[0]:
            paused[0]=True;s=json.loads((control/'state.json').read_text());s.update(desired='paused',version=1);(control/'state.json').write_text(json.dumps(s))
        return data
    def evaluated(*args,**kwargs):
        assert json.loads((control/'state.json').read_text())['desired']=='paused';evaluations.append(True);return {'complete':True}
    monkeypatch.setattr(ProcessEnv,'receive',received);monkeypatch.setattr(evaluation,'evaluate',evaluated)
    first=run(root,actor,max_updates=1,teacher_enabled=False,collection_rounds=4)
    assert first['rounds']==1 and first['completed_games']==50 and first['control_desired']=='paused'
    assert evaluations==[True] and first['last_evaluation']==50
    state=json.loads((control/'state.json').read_text());state.update(desired='running',version=2);(control/'state.json').write_text(json.dumps(state))
    second=run(root,actor,max_updates=1,teacher_enabled=False,collection_rounds=2)
    assert second['generation']==2 and second['rounds']==3 and second['control_desired']=='running'
