from collections import Counter
import torch,numpy as np
from learning.mission_schedule import schedule
from learning.mission_env import MissionEnv,MissionTeacher
from learning.mission_initialize import initialize
from learning.mission_state import save,load
from learning.league_policy import choose,update


def test_balanced_mixed_block():
    a=schedule(2);assert a==schedule(2) and a!=schedule(3);assert len(a)==96
    for mode in ('2','3','4'):
        rows=[r for r in a if r['scenario_id']==mode];assert len(rows)==32;assert Counter(r['kind'] for r in rows)=={'duel':16,'past':8,'algorithm':8}
        assert set(Counter((r['learner'],r['team'],r['swap'],r['kind']) for r in rows if r['kind']!='duel').values())=={1}


def test_checkpoint_and_independent_update(tmp_path):
    torch.set_num_threads(1);e=MissionEnv(scenario_id='4');e.reset(4);models=[initialize(81+i) for i in range(2)];buffers=[MissionTeacher(),MissionTeacher()];q=MissionTeacher();g=[torch.Generator().manual_seed(50+i) for i in range(2)]
    state=dict(generation=0,rules_version='combined-arms-5',catalog_version='combined-arms-3',contract='tactics-3',assignments={},run='test',completed_games=0)
    f=save(tmp_path,models,e,buffers,q,g,state);hash_before=e.engine.world.checksum();e2=MissionEnv();restored,st=load(tmp_path,e2,[MissionTeacher(),MissionTeacher()],MissionTeacher(),[torch.Generator(),torch.Generator()]);assert e2.scenario_id=='4' and hash_before==e2.engine.world.checksum()
    from learning.league_archive import spool,verify
    import hashlib
    archive=spool(tmp_path,f,state,True);assert verify(archive,hashlib.sha256(archive.read_bytes()).hexdigest(),True)
    x=e.vector('A');mask=e.mask('A');before=[p.detach().clone() for p in models[1].policy.parameters()];rows=[]
    for i in range(4):
        a,v,lp=choose(models[0],x,mask);rows.append(dict(obs=x,mask=mask,action=a,value=v,logp=lp,reward=.1,terminal=i==3,start=i==0,advance=i==3))
    update(models[0],rows,0,buffers[0]);assert all(torch.equal(p,b) for p,b in zip(models[1].policy.parameters(),before))
    assert choose(restored[1],x,mask,deterministic=True)==choose(models[1],x,mask,deterministic=True)


def test_runner_real_updates_and_resume_without_global_side_effects(tmp_path,monkeypatch):
    import learning.mission_league as league
    import learning.league_archive as archive
    import learning.results as results
    from learning.mission_policy import export
    from engine.multi_scenario import create
    torch.set_num_threads(1);monkeypatch.setenv('MW_NV_TORCH_THREADS','1');monkeypatch.delenv('MW_NV_PUBLISH_TRAINING',raising=False)
    source=tmp_path/'source';source.mkdir()
    for i in (1,2):m=initialize(i);m.save(source/f'ppo{i}.zip');export(m,source/f'ppo{i}.npz')
    def short(seed,swap=False):
        w=create(seed,swap,scenario_id='3');w.scenario['time_limit_s']=1;return w
    class ShortEnv(MissionEnv):
        def __init__(self,**kwargs):super().__init__(scenario_factory=short)
    class SilentReporter:
        def __init__(self,*args):pass
        def __call__(self,*args,**kwargs):pass
    monkeypatch.setattr(league,'CandidateEnv',ShortEnv);monkeypatch.setattr(league,'Reporter',SilentReporter);monkeypatch.setattr(archive,'spool',lambda *args,**kw:tmp_path);monkeypatch.setattr(archive,'publish_pending',lambda *_:dict(status='verified',failures=[]))
    world_record=results.record_world;training_record=results.record_training
    monkeypatch.setattr(results,'record_world',lambda db,*a,**kw:world_record(tmp_path/'isolated.sqlite',*a,**kw));monkeypatch.setattr(results,'record_training',lambda db,*a,**kw:training_record(tmp_path/'isolated.sqlite',*a,**kw))
    root=tmp_path/'run';state=league.run(root,source,max_updates=1,teacher_enabled=False,collection_rounds=2);assert state['generation']==1 and state['completed_games']==2
    assert state['ppo1_last_update']['steps']>0 and state['ppo2_last_update']['steps']>0
    restored=league.run(root,source,max_updates=1,teacher_enabled=False,collection_rounds=2);assert restored['generation']==2 and restored['completed_games']==4
