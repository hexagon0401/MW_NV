"""Single CPU coordinator: two independent PPOs, 10s tactics, paired 30s NIM."""
import argparse,json,os,random,signal,time,uuid,hashlib,shutil
from pathlib import Path
import numpy as np
import torch
RULES_VERSION='combined-arms-5'
CATALOG_VERSION='combined-arms-3'
from engine.viewer_export import frame
from .mission_env import MissionEnv as CandidateEnv
from .mission_numpy import NumpyPolicy as CandidatePolicy
from .mission_policy import export
from .training_maps import training_scenario
from .mission_env import MissionTeacher as TeacherBuffer
from .league_policy import choose,update
from .mission_schedule import schedule
from .mission_initialize import initialize
from .mission_state import save,load,record_update
from .league_metrics import new_metrics,opportunity,selection,finish
from .self_play import atomic_json,current
from .training_status import Reporter


def assignments(descriptor):
    team=descriptor['team'];other='B' if team=='A' else 'A'
    if descriptor['kind']=='duel':return {team:'PPO1',other:'PPO2'}
    return {team:f'PPO{descriptor["learner"]+1}',other:descriptor['kind']}


def run(root,source,pilot=192,teacher_enabled=True,max_updates=0,collection_rounds=64):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    gate=root/'validation-gates.json'
    if not max_updates and (not gate.exists() or not json.loads(gate.read_text()).get('approved_for_pilot')):raise ValueError('mixed training blocked: incomplete engine/migration validation gates')
    for name in ('opponents','baseline','evaluations','insights'): (root/name).mkdir(exist_ok=True)
    if (root/'results.sqlite').exists() and not (root/'ledger-imported').exists():
        import sqlite3
        from .results import SCHEMA
        Path('data').mkdir(exist_ok=True)
        with sqlite3.connect('data/results.sqlite') as conn:
            conn.execute(SCHEMA);conn.execute('ATTACH DATABASE ? AS restored',(str((root/'results.sqlite').resolve()),))
            if conn.execute('SELECT count(*) FROM records r JOIN restored.records s ON r.id=s.id WHERE r.payload!=s.payload').fetchone()[0]:raise ValueError('restored ledger conflict')
            conn.execute('INSERT OR IGNORE INTO records SELECT * FROM restored.records');conn.commit()
        (root/'ledger-imported').write_text('verified merge')
    torch.set_num_threads(int(os.environ.get('MW_NV_TORCH_THREADS','2')))
    buffers=[TeacherBuffer(),TeacherBuffer()];querier=TeacherBuffer();generators=[torch.Generator().manual_seed(902+i) for i in range(2)]
    env=CandidateEnv(decision_seconds=10)
    if (root/'current.json').exists():models,state=load(root,env,buffers,querier,generators)
    else:
        models=[]
        from sb3_contrib import MaskablePPO
        from stable_baselines3.common.logger import configure
        for i in range(2):
            model=MaskablePPO.load(Path(source)/f'ppo{i+1}.zip',device='cpu');model.set_logger(configure(folder=None,format_strings=[]));models.append(model)
        env.reset(0)
        state=dict(schema=1,run='league-'+uuid.uuid4().hex[:12],rules_version=RULES_VERSION,catalog_version=CATALOG_VERSION,contract='tactics-3',map_id='mixed-2-3-4',map_version='1',generation=0,completed_games=0,episode=0,active=False,initial_frame=None,metrics=None,assignments={},policy_spans={},episode_starts={},rounds=0,last_policy_archive=0,last_full_archive=0,last_evaluation=-1,pilot=pilot,teacher_enabled=teacher_enabled,source_sha256=[hashlib.sha256((Path(source)/f'ppo{i+1}.npz').read_bytes()).hexdigest() for i in range(2)])
        for i,m in enumerate(models):
            export(m,root/'baseline'/f'ppo{i+1}.npz');m.save(root/'baseline'/f'ppo{i+1}.zip')
        save(root,models,env,buffers,querier,generators,state)
    if state.get('runtime_schema')=='adaptive-1':raise ValueError('adaptive checkpoint: resume with learning.accelerated_league')
    import subprocess
    revision=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()
    if revision and revision!=state.get('code_commit'):
        state.setdefault('code_commits',[]).append(revision);state['code_commit']=revision
    record_update(root,state,models)
    state['teacher_enabled']=teacher_enabled;state['pilot']=pilot
    stop={'value':False}
    def on_stop(*_):stop['value']=True
    old={s:signal.signal(s,on_stop) for s in (signal.SIGINT,signal.SIGTERM)}
    reporter=Reporter(root,state['generation'],sum(m.num_timesteps for m in models));start=time.monotonic();simulated=0;updates=0
    def report(phase='learning',force=False):
        if phase=='evaluation' and (stop['value'] or (root/'STOP').exists()):raise InterruptedError('evaluation paused at simulation boundary')
        evaluation_cases=0
        if phase=='evaluation':
            progress_path=root/'evaluations'/f'games-{state["completed_games"]:08d}'/'report.json'
            if progress_path.exists():evaluation_cases=len(json.loads(progress_path.read_text())['results'])
        reporter.round=state['generation'];reporter.base_steps=sum(m.num_timesteps for m in models)
        reporter(dict(phase=phase,status='running',games=state['completed_games'],policy_steps=reporter.base_steps,sim_seconds=simulated,algorithm='Independent multi-mode MaskablePPO',maps='3 balanced mission modes',learners=[dict(id=f'PPO{i+1}',steps=m.num_timesteps,teacher_samples=len(buffers[i].rows),imitation_updates=buffers[i].stats.get('imitation_updates',0)) for i,m in enumerate(models)],teacher=dict(querier.stats),nim_in_training=teacher_enabled,decision_seconds=10,teacher_seconds=30,game_mode=getattr(env.engine.world,'mode','conquest'),scenario_id=env.scenario_id,initial_evaluation_parallel=False,evaluation_cases=evaluation_cases,evaluation_total=240,backup=state.get('backup','pending'),pilot=pilot,assignments=state['assignments'],rules_version=RULES_VERSION,map_id='mixed-2-3-4',map_version='1'),force=force)
    if hasattr(reporter,'advance_simulation'):report.advance_simulation=reporter.advance_simulation
    def teach(e):
        if not teacher_enabled:return
        querier.rows.clear();querier.collect(e)
        for row in querier.rows:
            learner=state['assignments'].get(('A','B')[row[3]])
            if learner in ('PPO1','PPO2'):buffers[int(learner[-1])-1].rows.append(row)
        querier.rows.clear()
    env.teacher_hook=teach
    def begin():
        descriptor=schedule(state['episode']//96)[state['episode']%96];state['descriptor']=descriptor;state['assignments']=assignments(descriptor)
        if descriptor['kind']=='past':
            files=sorted((root/'opponents').glob('*.npz'));options=files if files and random.random()>=.5 else sorted((root/'baseline').glob('*.npz'))
            state['fixed_opponent']=str(random.choice(options).relative_to(root))
        else:state['fixed_opponent']=None
        state['policy_spans']={a:[state['generation']] for a,l in state['assignments'].items() if l in ('PPO1','PPO2')};state['episode_starts']={a:True for a in ('A','B')};state['metrics']=new_metrics()
        # Map family is independently scheduled, not coupled to team/opponent.
        env.scenario_id=descriptor['scenario_id'];env.reset(seed=descriptor['seed'],options={'swap':descriptor['swap']});state['initial_frame']=frame(env.engine.world);state['active']=True
    try:
        # Evaluation is resumable and never consumes training/teacher samples.
        from .mission_evaluate import evaluate
        from .mission_evaluate import initial_complete,ensure_initial_worker
        if not state.get('initial_archived'):
            from .league_archive import spool,publish_pending
            spool(root,current(root),state,True);initial_archive=publish_pending(root);state['backup']='verified' if initial_archive['status']=='verified' else 'deferred:archive';state['initial_archived']=initial_archive['status']=='verified'
            save(root,models,env,buffers,querier,generators,state)
        if state['last_evaluation']<0:
            state['last_evaluation']=0;save(root,models,env,buffers,querier,generators,state)
        baseline_running=ensure_initial_worker(root,state) if not max_updates else False
        state['initial_evaluation_parallel']=baseline_running
        torch.set_num_threads(1 if baseline_running else int(os.environ.get('MW_NV_TORCH_THREADS','2')))
        while (not max_updates or updates<max_updates) and not stop['value'] and not (root/'STOP').exists():
            if not max_updates:
                baseline_running=ensure_initial_worker(root,state);state['initial_evaluation_parallel']=baseline_running
                torch.set_num_threads(1 if baseline_running else int(os.environ.get('MW_NV_TORCH_THREADS','2')))
            rows=[[],[]]
            for _ in range(collection_rounds):
                if not state['active']:begin()
                try:fixed=CandidatePolicy(root/state['fixed_opponent']) if state['fixed_opponent'] else None
                except (OSError,ValueError):fixed=None;state['past_policy_error']='algorithm fallback'
                last={};before=env.engine.world.tick
                for a in ('A','B'):opportunity(state['metrics'],a,env.items[a])
                while not all(env.finished.values()):
                    actions={}
                    for a in ('A','B'):
                        if env.finished[a]:continue
                        learner=state['assignments'][a];observation=env.vector(a);mask=env.mask(a)
                        if learner in ('PPO1','PPO2'):
                            i=int(learner[-1])-1;action,value,logp=choose(models[i],observation,mask,generators[i])
                            record=dict(obs=observation.copy(),mask=mask.copy(),action=action,value=value,logp=logp,reward=0.,terminal=False,advance=False,start=state['episode_starts'][a]);state['episode_starts'][a]=False;rows[i].append(record);last[a]=record
                        else:action=fixed.predict(observation,mask) if fixed else env.heuristic(a)
                        if action!=64:selection(state['metrics'],a,next(c for c in env.items[a] if c['id']==action),before)
                        actions[a]=action
                    env.decision_sources={a:(learner+' 지휘' if learner in ('PPO1','PPO2') else '과거 정책' if learner=='past' else '규칙 지휘') for a,learner in state['assignments'].items()}
                    _,rewards,done,_,_=env.step(actions)
                    # _round resets finished after advancing; time, not flags, is the barrier.
                    if env.engine.world.tick!=before or not env.agents:
                        for a,record in last.items():record.update(reward=float(rewards[a]),terminal=not bool(env.agents),advance=True)
                        break
                state['rounds']+=1;simulated+=(env.engine.world.tick-before)*.2
                if not env.agents:
                    from .results import record_world
                    policies={}
                    for a,learner in state['assignments'].items():
                        if learner in ('PPO1','PPO2'):
                            i=int(learner[-1])-1;identity=root/f'identity{i}.npz';export(models[i],identity);policies[a]=CandidatePolicy(identity).policy_id;identity.unlink()
                        else:policies[a]=fixed.policy_id if fixed else 'algorithm'
                    metadata=dict(run=state['run'],episode=state['episode'],assignments=state['assignments'],descriptor=state['descriptor'],generation=state['generation'],policy_spans=state['policy_spans'],metrics=finish(state['metrics'],env.engine.world,state['initial_frame']))
                    record_world('data/results.sqlite',env.engine.world,'training',policies,match_id=f'{state["run"]}-{state["episode"]:08d}',initial_frame=state['initial_frame'],metadata={'league':metadata})
                    state['completed_games']+=1;state['episode']+=1;state['active']=False
                    if os.environ.get('MW_NV_PUBLISH_TRAINING')=='1':
                        try:
                            from .replay_sink import publish_latest
                            publish_latest(env.engine,state['initial_frame'],metadata={'league':dict(run=state['run'],assignments=state['assignments'],generation=state['generation'])})
                        except (OSError,ValueError) as exc:state['replay_publish_error']=type(exc).__name__
                report()
                if stop['value'] or (root/'STOP').exists():break
                if state['completed_games']>=pilot and not state.get('pilot_report'):break
            # Both actors remained fixed for the entire collection interval.
            for i,m in enumerate(models):
                team=next((a for a,l in state['assignments'].items() if l==f'PPO{i+1}'),None)
                last_value=choose(m,env.vector(team),env.mask(team),deterministic=True)[1] if state['active'] and team else 0.
                result=update(m,rows[i],last_value,buffers[i]);state[f'ppo{i+1}_last_update']=result
                if state['active'] and team:state['policy_spans'].setdefault(team,[]).append(state['generation'])
                export(m,root/'opponents'/f'ppo{i+1}-{state["generation"]:08d}.npz')
                paths=sorted((root/'opponents').glob(f'ppo{i+1}-*.npz'))
                for p in paths[:-8]:
                    if str(p.relative_to(root))!=state.get('fixed_opponent'):p.unlink()
            state['generation']+=1;checkpoint=save(root,models,env,buffers,querier,generators,state);record_update(root,state,models);updates+=1
            from .league_archive import spool,publish_pending
            created_archive=False
            if state['completed_games']-state['last_policy_archive']>=10 or state['generation']-state.get('last_policy_update',0)>=24:
                spool(root,checkpoint,state);created_archive=True;state['last_policy_update']=state['generation'];state['last_policy_archive']=state['completed_games']//10*10
            if state['completed_games']-state['last_full_archive']>=50 or state['generation']-state.get('last_full_update',0)>=120:
                spool(root,checkpoint,state,True);created_archive=True;state['last_full_update']=state['generation'];state['last_full_archive']=state['completed_games']//50*50
            if created_archive or time.time()>=state.get('archive_retry_at',0):
                archive=publish_pending(root);state['backup']='verified' if archive['status']=='verified' and list((root/'archive-verified').glob('*.json')) else 'deferred:archive' if archive['failures'] else 'pending';state['archive_retry_at']=time.time()+300
            if state['completed_games']//96>state['last_evaluation']//96:
                report('evaluation',True);evaluate(root,models,state,report);state['last_evaluation']=state['completed_games']//96*96
                while not initial_complete(root):
                    ensure_initial_worker(root,state);report('evaluation',True);time.sleep(5)
                from .mission_evaluate import pilot_report
                interim=pilot_report(root,state)
                if interim['pause']:state['pause_reason']='mode_regression';stop['value']=True
            if state['completed_games']>=pilot and not state.get('pilot_report'):
                from .mission_evaluate import pilot_report
                if not initial_complete(root):raise ValueError('missing initial evaluation')
                verdict=pilot_report(root,state);state['pilot_report']=verdict
                if verdict['pause']:state['pause_reason']='pilot_regression';stop['value']=True
                elif any(v and v['mean']>0 for v in verdict.get('modes',{}).values()):
                    from .mission_evaluate import confirm
                    report('evaluation',True);state['confirmation']=confirm(root,models,state,report)
            save(root,models,env,buffers,querier,generators,state);report('checkpoint_saved',True)
    except InterruptedError:
        pass
    finally:
        if stop['value'] or (root/'STOP').exists():
            try:
                pid=int((root/'initial-evaluation.pid').read_text());cmd=(Path('/proc')/str(pid)/'cmdline').read_bytes()
                if b'learning.mission_evaluate' in cmd:os.kill(pid,signal.SIGTERM)
            except (OSError,ValueError):pass
        for s,h in old.items():signal.signal(s,h)
        reporter(dict(phase='stopped',status='stopped',games=state['completed_games']),force=True)
    return state

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='data/multi-mode-v1');p.add_argument('--source',required=True);p.add_argument('--pilot',type=int,default=192);p.add_argument('--updates',type=int,default=0);p.add_argument('--no-teacher',action='store_true');a=p.parse_args()
    import fcntl
    Path(a.root).mkdir(parents=True,exist_ok=True)
    lock=(Path(a.root)/'runner.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('multi-mode worker already running')
    (Path(a.root)/'runner.pid').write_text(str(os.getpid()))
    run(a.root,a.source,a.pilot,not a.no_teacher,a.updates)
