"""Long-lived shared PPO, frozen opponents, paired NIM labels and resumable environment."""
import argparse,json,os,random,shutil,time,uuid,signal
from pathlib import Path
import numpy as np
import torch
from stable_baselines3.common.callbacks import BaseCallback
from .candidate_train import TrainingEnv
from .candidate_policy import CandidatePolicy,export
from .teacher import TeacherPPO,TeacherBuffer
from .training_status import Reporter
from engine.runtime import Engine
from engine.replay import encode,decode

class SelfPlayEnv(TrainingEnv):
    def __init__(self,root,teacher):
        super().__init__(stats='data/results.sqlite');self.root=Path(root);self.teacher=teacher;self.completed_games=0;self.parallel.teacher_hook=teacher.collect
    def reset(self,seed=None,options=None):
        # Four combinations per seed: neither team letter nor terrain family fixes a starting side.
        n=self.episode;self.controlled='A' if n%2==0 else 'B';self.other='B' if self.controlled=='A' else 'A'
        choice=n%4;files=sorted((self.root/'opponents').glob('*.npz'))
        path=self.root/'champion.npz' if choice<2 else random.choice(files) if choice==2 and files else None
        self.opponent=CandidatePolicy(path) if path else None
        result=super().reset(seed=(n//4)%50,options={'swap':bool((n//2)%2)});self.match_id=f'{self.run_id}-{n}';return result
    def step(self,action):
        result=super().step(action)
        if result[2] and getattr(self,'last_match_inserted',True):self.completed_games+=1
        return result
    def snapshot(self):
        p=self.parallel
        return encode(dict(world=p.engine.world,presentation_events=p.engine.presentation_events,agents=p.agents,items=p.items,selected=p.selected,finished=p.finished,reserved_supply=p.reserved_supply,initial_costs=p.initial_costs,controlled=self.controlled,other=self.other,episode=self.episode,completed_games=self.completed_games,games=self.games,sim_seconds=self.sim_seconds,run_id=self.run_id,initial_frame=self.initial_frame,match_id=self.match_id,opponent_weights=None if self.opponent is None else {k:v.tolist() for k,v in self.opponent.weights.items()},opponent_id=None if self.opponent is None else self.opponent.policy_id))
    def restore(self,document):
        d=decode(document);world=d.pop('world')
        from engine.version import RULES_VERSION,CATALOG_VERSION
        if world.rules_version!=RULES_VERSION or world.catalog_version!=CATALOG_VERSION:raise ValueError('incompatible recovery rules/catalog')
        if getattr(world,'map_id',None)=='river-districts' and getattr(world,'map_version',None)!='2':raise ValueError('incompatible recovery map version')
        p=self.parallel;p.engine=Engine(world);p.engine.presentation_events=d.pop('presentation_events',[])
        for k in ('agents','items','selected','finished','reserved_supply','initial_costs'):setattr(p,k,d.pop(k))
        weights=d.pop('opponent_weights');identity=d.pop('opponent_id');self.opponent=None
        if weights:
            self.opponent=CandidatePolicy.__new__(CandidatePolicy);self.opponent.weights={k:np.asarray(v,dtype=np.float32) for k,v in weights.items()};self.opponent.policy_id=identity
        for k,v in d.items():setattr(self,k,v)

def atomic_json(path,value):
    path=Path(path);tmp=path.with_suffix('.partial');tmp.write_text(json.dumps(value));tmp.replace(path)

def current(root):
    root=Path(root)
    if (root/'current.json').exists():return root/json.loads((root/'current.json').read_text())['path']
    return root

def checkpoint(root,model,env,teacher,state):
    root=Path(root);parent=root/'checkpoints';parent.mkdir(exist_ok=True)
    directory=parent/f"checkpoint-{state['generation']:08d}-{uuid.uuid4().hex[:8]}";directory.mkdir()
    model.save(directory/'latest.zip');export(model,directory/'latest.npz')
    observation=env.parallel.vector(env.controlled);mask=env.parallel.mask(env.controlled)
    assert int(model.predict(observation,deterministic=True,action_masks=mask)[0])==CandidatePolicy(directory/'latest.npz').predict(observation,mask)
    teacher.save(directory/'teacher.npz')
    state['teacher_stats']=dict(teacher.stats)
    atomic_json(directory/'environment.json',env.snapshot())
    monitor=model.get_env().envs[0]
    atomic_json(directory/'monitor.json',{k:getattr(monitor,k) for k in ('needs_reset','rewards','total_steps','episode_returns','episode_lengths','episode_times') if hasattr(monitor,k)})
    npstate=np.random.get_state()
    atomic_json(directory/'rng.json',dict(python=encode(random.getstate()),numpy=[npstate[0],npstate[1].tolist(),*npstate[2:]],torch=torch.get_rng_state().tolist()))
    for role in ('A','B'):atomic_json(directory/f'{role}.json',dict(role=role,shared_policy='latest.npz',assigned_policy='shared' if role==env.controlled else env.opponent.policy_id if env.opponent else 'algorithm',generation=state['generation'],rules_version=env.parallel.engine.world.rules_version,opponent=env.opponent.policy_id if env.opponent else 'algorithm'))
    if Path('data/results.sqlite').exists():
        import sqlite3
        with sqlite3.connect('data/results.sqlite') as source,sqlite3.connect(directory/'results.sqlite') as dest:source.backup(dest)
    atomic_json(directory/'state.json',state)
    atomic_json(root/'current.json',dict(path=str(directory.relative_to(root))))
    atomic_json(root/'state.json',state)
    if os.environ.get('MW_NV_PUBLISH_TRAINING')=='1':
        try:
            from cloud.supabase_storage import PrivateStorage
            store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY'])
            for role in ('A','B'):store._request('object/'+store.bucket+'/'+role+'.json','PUT',(directory/f'{role}.json').read_bytes())
        except (OSError,ValueError,KeyError):state['role_metadata_upload']='deferred'
    for old in sorted(parent.glob('checkpoint-*'),key=lambda p:p.stat().st_mtime)[:-2]:shutil.rmtree(old)
    return directory

def backup_due(completed,last,retry_at=0,now=None):return completed-last>=10 and (time.time() if now is None else now)>=retry_at

def run(root,seed_policy,updates=0,teacher_enabled=True,publish=True):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);(root/'opponents').mkdir(exist_ok=True)
    if (root/'results.sqlite').exists() and not (root/'ledger-imported').exists():
        import sqlite3
        from .results import SCHEMA
        with sqlite3.connect('data/results.sqlite') as conn:
            conn.execute(SCHEMA);conn.execute('ATTACH DATABASE ? AS restored',(str(root/'results.sqlite'),));conn.execute('INSERT OR IGNORE INTO records SELECT * FROM restored.records');conn.commit()
        (root/'ledger-imported').write_text('restored')
    torch.set_num_threads(2);teacher=TeacherBuffer();env=SelfPlayEnv(root,teacher)
    if not teacher_enabled:env.parallel.teacher_hook=lambda e:None
    if not (root/'champion.npz').exists():shutil.copyfile(Path(seed_policy).with_suffix('.npz'),root/'champion.npz')
    state=dict(schema=2,generation=0,completed_games=0,last_backup_games=0,last_evaluation_games=0)
    saved=current(root)
    if (saved/'state.json').exists():
        state=json.loads((saved/'state.json').read_text());env.restore(json.loads((saved/'environment.json').read_text()));teacher.load(saved/'teacher.npz');teacher.stats.update(state.get('teacher_stats',{}))
        model=TeacherPPO.load(saved/'latest.zip',env=env,device='cpu',force_reset=False)
        monitor=model.get_env().envs[0]
        data=json.loads((saved/'monitor.json').read_text()) if (saved/'monitor.json').exists() else dict(needs_reset=False,rewards=[])
        for k,v in data.items():setattr(monitor,k,v)
        rng=json.loads((saved/'rng.json').read_text());random.setstate(decode(rng['python']));n=rng['numpy'];np.random.set_state((n[0],np.array(n[1],dtype=np.uint32),*n[2:]));torch.set_rng_state(torch.tensor(rng['torch'],dtype=torch.uint8))
    else:model=TeacherPPO.load(seed_policy,env=env,device='cpu');model.set_random_seed(0)
    if Path('data/results.sqlite').exists():
        import sqlite3
        with sqlite3.connect('data/results.sqlite') as conn:
            try:env.completed_games=max(env.completed_games,conn.execute("SELECT count(*) FROM records WHERE kind='match' AND id LIKE ?",(env.run_id+'-%',)).fetchone()[0])
            except sqlite3.OperationalError:pass
    import subprocess
    from engine.version import RULES_VERSION,CATALOG_VERSION
    state.update(rules_version=RULES_VERSION,catalog_version=CATALOG_VERSION,policy_contract='tactics-1',map_id='river-districts',map_version='2',code_commit=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip())
    model.teacher_buffer=teacher;report=Reporter(root,state['generation'],model.num_timesteps);start_steps=model.num_timesteps;started_sim=env.sim_seconds;finished=0
    class Progress(BaseCallback):
        def _on_step(self):
            report(dict(phase='learning',policy_steps=self.num_timesteps,sim_seconds=env.sim_seconds-started_sim,games=env.completed_games,nim_in_training=teacher_enabled,teacher=dict(teacher.stats),backup=state.get('backup','pending'),map_family=getattr(env.parallel.engine.world,'training_map_family','custom'),map_id=getattr(env.parallel.engine.world,'map_id',None),map_version=getattr(env.parallel.engine.world,'map_version',None)))
            return True
    stop_requested={'value':False}
    def request_stop(signum,frame):stop_requested['value']=True
    previous_handlers={s:signal.signal(s,request_stop) for s in (signal.SIGINT,signal.SIGTERM)}
    try:
        while (updates==0 or finished<updates) and not stop_requested['value'] and not (root/'STOP').exists():
            report.round=state['generation'];report(dict(phase='learning',nim_in_training=teacher_enabled,policy_steps=model.num_timesteps,sim_seconds=env.sim_seconds-started_sim,games=env.completed_games,teacher=dict(teacher.stats),backup=state.get('backup','pending')),force=True)
            before_steps=model.num_timesteps
            model.learn(total_timesteps=64,reset_num_timesteps=False,callback=Progress())
            state.update(generation=state['generation']+1,completed_games=env.completed_games,policy_steps=model.num_timesteps)
            report.base_steps=model.num_timesteps
            from .results import record_training
            identity=root/'identity.npz';export(model,identity);policy_id=CandidatePolicy(identity).policy_id;identity.unlink()
            record_training('data/results.sqlite',policy_id,model.num_timesteps-before_steps,env.opponent.policy_id if env.opponent else 'algorithm',run_id=f'{env.run_id}-update-{state["generation"]}-{policy_id}',training_run=env.run_id)
            checkpoint(root,model,env,teacher,state)
            # Frozen opponent snapshots are bounded and never modified during an episode.
            if state['generation']%4==0:
                shutil.copyfile(current(root)/'latest.npz',root/'opponents'/f'policy-{state["generation"]:08d}.npz')
                for path in sorted((root/'opponents').glob('*.npz'))[:-8]:path.unlink()
            atomic_json(root/'opponents.json',dict(files=[p.name for p in sorted((root/'opponents').glob('*.npz'))]))
            if publish and backup_due(env.completed_games,state['last_backup_games'],state.get('backup_retry_at',0)):
                try:
                    from .backup import publish as backup
                    previous_backup=state['last_backup_games'];backup(root,state['generation']);state['last_backup_games']=env.completed_games;state['backup']='verified';state['backup_retry_at']=0;checkpoint(root,model,env,teacher,state)
                except Exception as exc:
                    state['last_backup_games']=previous_backup;state['backup']='deferred:'+type(exc).__name__;state['backup_retry_at']=time.time()+300;checkpoint(root,model,env,teacher,state)
            if env.completed_games-state['last_evaluation_games']>=50:
                report(dict(phase='evaluation'),force=True)
                from .self_play_evaluate import evaluate
                evaluate(root,state['generation']);state['last_evaluation_games']=env.completed_games
            atomic_json(root/'state.json',state);report(dict(phase='checkpoint_saved',nim_in_training=teacher_enabled,policy_steps=model.num_timesteps,games=env.completed_games),force=True);finished+=1
    finally:
        for signum,handler in previous_handlers.items():signal.signal(signum,handler)
        report(dict(status='stopped',phase='stopped',nim_in_training=teacher_enabled),force=True)

    # Any interruption before a consumed checkpoint restores the last safe generation.
    return state

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='data/self-play-v3');p.add_argument('--seed-policy',required=True);p.add_argument('--updates',type=int,default=0);p.add_argument('--no-teacher',action='store_true');p.add_argument('--no-publish',action='store_true');a=p.parse_args();run(a.root,a.seed_policy,a.updates,not a.no_teacher,not a.no_publish)
