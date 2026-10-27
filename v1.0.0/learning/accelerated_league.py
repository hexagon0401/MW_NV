"""Adaptive process rollouts; independent frozen PPOs, async teacher and durable I/O."""
import argparse,gzip,hashlib,importlib,json,os,random,signal,time,uuid
from pathlib import Path
import numpy as np
import torch
from .process_env import ProcessEnv,make_env,snapshot,restore
from .adaptive_resources import Adaptive,resources
from .async_teacher import AsyncTeacher
from . import background_io as io
from .league_policy import choose,update,advantages
from .league_metrics import finish
from .self_play import atomic_json,current
from .training_status import Reporter
from .checkpoint_io import commit_metadata
from engine.replay import decode
from server import ppo_control as control


def trajectory_rows(model,paths,packets):
    rows=[]
    for (index,episode,team),trajectory in sorted(paths.items()):
        last_value=0. if trajectory[-1]['terminal'] else choose(model,packets[index]['vectors'][team],packets[index]['masks'][team],deterministic=True)[1]
        for row,adv in zip(trajectory,advantages(trajectory,last_value)):row['advantage']=float(adv)
        rows.extend(trajectory)
    return rows


def run(root,source,kind='legacy',pilot=200,max_updates=0,teacher_enabled=True,fixed_workers=None,collection_rounds=64):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);torch.set_num_threads(1)
    if os.environ.get('MW_NV_EXPERIMENT_SEED'):
        experiment_seed=int(os.environ['MW_NV_EXPERIMENT_SEED']);random.seed(experiment_seed);np.random.seed(experiment_seed);torch.manual_seed(experiment_seed)
    if (root/'results.sqlite').exists() and not (root/'ledger-imported').exists():
        import sqlite3
        from .results import SCHEMA
        Path('data').mkdir(exist_ok=True)
        with sqlite3.connect('data/results.sqlite') as conn:
            conn.execute(SCHEMA);conn.execute('ATTACH DATABASE ? AS restored',(str((root/'results.sqlite').resolve()),))
            if conn.execute('SELECT count(*) FROM records r JOIN restored.records s ON r.id=s.id WHERE r.payload!=s.payload').fetchone()[0]:raise ValueError('restored ledger conflict')
            conn.execute('INSERT OR IGNORE INTO records SELECT * FROM restored.records');conn.commit()
        (root/'ledger-imported').write_text('verified merge')
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
    os.environ['MW_NV_ASYNC_IO']='1'
    backend=importlib.import_module('.mission_league' if kind=='mission' else '.league',__package__)
    evaluation=importlib.import_module('.mission_evaluate' if kind=='mission' else '.league_evaluate',__package__)
    if kind=='mission' and not max_updates:
        gate=root/'validation-gates.json'
        if not gate.exists() or not json.loads(gate.read_text()).get('approved_for_pilot'):raise ValueError('T11 validation gates required')
        from .mission_rollout import code_fingerprint
        if json.loads(gate.read_text()).get('code_sha256')!=code_fingerprint():raise ValueError('T11 validation gate belongs to different code')
    exploring=kind=='mission' and os.environ.get('MW_NV_EXPLORATION')=='1'
    if exploring:
        proof=json.loads((root/'strategy-gates.json').read_text())
        from .mission_rollout import code_fingerprint
        if not proof.get('approved_for_exploration') or proof.get('code_sha256')!=code_fingerprint():raise ValueError('completed pilot exploration certificate required')
        if not (root/'current.json').exists() and any(hashlib.sha256((Path(source)/name).read_bytes()).hexdigest()!=digest for name,digest in proof.get('initialized_sha256',{}).items()):raise ValueError('successor initialization changed')
        # Demonstration workers currently store tactics-4 labels; never mix contracts.
        if teacher_enabled and os.environ.get('MW_NV_DISABLE_MISSION_COACH')!='1':raise ValueError('tactics-5 supports ordinary teacher only until demonstration history parity passes')
    for name in ('opponents','baseline','evaluations','insights'):(root/name).mkdir(exist_ok=True)
    buffer_class=backend.TeacherBuffer
    if kind=='mission' and os.environ.get('MW_NV_EXPLORATION')=='1':
        from .exploration_env import ExplorationTeacher
        buffer_class=ExplorationTeacher
    buffers=[buffer_class(),buffer_class()];query=buffer_class();generators=[torch.Generator().manual_seed(902+i) for i in range(2)]
    env=make_env(kind)
    if (root/'current.json').exists():models,state=backend.load(root,env,buffers,query,generators)
    else:
        if kind=='legacy':models=[backend.initialize(source,41+i) for i in range(2)]
        else:
            from sb3_contrib import MaskablePPO
            from stable_baselines3.common.logger import configure
            models=[MaskablePPO.load(Path(source)/f'ppo{i+1}.zip',device='cpu') for i in range(2)]
            for m in models:m.set_logger(configure(folder=None,format_strings=[]))
        env.reset(0)
        state=dict(schema=1,run='league-'+uuid.uuid4().hex[:12],rules_version=backend.RULES_VERSION,catalog_version=backend.CATALOG_VERSION,contract=getattr(env,'contract','tactics-4') if kind=='mission' else 'tactics-2',map_id='mixed-2-3-4' if kind=='mission' else 'river-districts',map_version='1' if kind=='mission' else '2',generation=0,completed_games=0,episode=0,active=False,rounds=0,last_policy_archive=0,last_full_archive=0,last_evaluation=0,assignments={},teacher_enabled=teacher_enabled)
        for i,m in enumerate(models):
            backend.export(m,root/'baseline'/f'ppo{i+1}.npz')
            if kind=='mission':m.save(root/'baseline'/f'ppo{i+1}.zip')
        backend.save(root,models,env,buffers,query,generators,state)
    from .mission_coach import MissionCoach
    coach=MissionCoach(root) if kind=='mission' and teacher_enabled and os.environ.get('MW_NV_MISSION_TEACHER_BASELINE')!='1' and os.environ.get('MW_NV_DISABLE_MISSION_COACH')!='1' else None
    state['pilot']=pilot;state['teacher_enabled']=teacher_enabled
    control.register(root,source,kind,pilot,state['run'],state.get('control_desired'))
    state.setdefault('last_policy_update',state['generation']);state.setdefault('last_full_update',state['generation'])
    import subprocess
    revision=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()
    if revision!=state.get('code_commit'):state.setdefault('code_commits',[]).append(revision);state['code_commit']=revision
    backend.record_update(root,state,models)
    folder=current(root);extra=folder/'environments.json.gz';slots=[];next_episode=state.get('next_episode',state['episode']+int(state.get('active',False)))
    if extra.exists():
        with gzip.open(extra,'rt') as f:bundles=decode(json.load(f))
    else:
        info={k:state.get(k) for k in ('descriptor','assignments','fixed_opponent','initial_frame','metrics','episode_starts','policy_spans')}
        info.update(episode=state['episode'],generation=state['generation'],active=state.get('active',False))
        bundles=[dict(environment=snapshot(env),info=info,actor_rng=[g.get_state().tolist() for g in generators])]
    query.rows.clear();teacher=AsyncTeacher(query,buffers);adaptive=Adaptive();stop={'value':False};updates=0;simulated=0.;completed_start=state['completed_games'];started=time.monotonic();evaluation_games=state['completed_games'];worker_sim={};packets={};fixed_cache={}
    old_handlers={s:signal.signal(s,lambda *_:stop.update(value=True)) for s in (signal.SIGINT,signal.SIGTERM)}
    reporter=Reporter(root,state['generation'],sum(m.num_timesteps for m in models))
    publish=os.environ.get('MW_NV_PUBLISH_TRAINING')=='1'
    if publish:io.start(root)
    def stopped():return stop['value'] or (root/'STOP').exists()
    def add_slot(bundle=None):
        index=len(slots);worker=ProcessEnv(kind)
        gs=[torch.Generator().manual_seed(902+i+100003*index) for i in range(2)]
        info=dict(active=False)
        if bundle:
            info=bundle['info'];packets[index]=worker.call('load',bundle)
            for g,value in zip(gs,bundle['actor_rng']):g.set_state(torch.tensor(value,dtype=torch.uint8))
        slots.append(dict(worker=worker,info=info,generators=gs));worker_sim[index]=0.
    for bundle in bundles:
        bundle['info']['run_id']=state['run'];add_slot(bundle)
    def begin(index):
        nonlocal next_episode
        slot=slots[index];block_size=96 if kind=='mission' else 32;descriptor=backend.schedule(next_episode//block_size)[next_episode%block_size]
        assignment=backend.assignments(descriptor);fixed=None
        if descriptor['kind']=='past':
            picker=random.Random(4903+next_episode) if kind=='mission' else random
            files=sorted((root/'opponents').glob('*.npz'));options=files if files and picker.random()>=.5 else sorted((root/'baseline').glob('*.npz'));fixed=str(picker.choice(options).relative_to(root))
        if exploring and descriptor['kind']=='past':
            from .opponent_population import Population,fetch_remote
            population=Population(root);population.sync_verified()
            if population.state['entries']:
                entry=population.choose(next_episode,f'PPO{descriptor["learner"]+1}');fixed=str(population.resolve(entry,fetch_remote).relative_to(root))
                population.prune([Path(fixed).name,*[Path(s['info']['fixed_opponent']).name for s in slots if s['info'].get('fixed_opponent')]])
        info=dict(run_id=state['run'],active=True,episode=next_episode,descriptor=descriptor,assignments=assignment,fixed_opponent=fixed,generation=state['generation'],episode_starts={'A':True,'B':True})
        slot['info']=info;next_episode+=1;packets[index]=slot['worker'].call('reset',info)
    last_phase={'value':None}
    def report(phase='learning',force=False):
        category='evaluation' if phase=='evaluation' else 'paused' if phase=='paused' else 'learning'
        if category!=last_phase['value']:
            for index,slot in enumerate(slots):
                mark='PAUSED' if category=='paused' else 'WAITING' if category=='evaluation' or index>=adaptive.workers else 'RUNNING'
                slot['worker'].call('mark',mark)
            last_phase['value']=category
        if phase=='evaluation' and stopped():raise InterruptedError('evaluation paused at boundary')
        elapsed=max(.001,time.monotonic()-started);cases=0
        p=root/'evaluations'/f'games-{evaluation_games:08d}'/'report.json'
        if phase=='evaluation' and p.exists():cases=len(json.loads(p.read_text())['results'])
        publication={}
        for lane in ('publish','archive'):
            try:publication[lane]=json.loads((root/'io-jobs'/(lane+'-status.json')).read_text())
            except (OSError,ValueError):publication[lane]={'status':'pending'}
        publication['queued_archives']=len(list((root/'io-jobs/archives').glob('[!.]*')))
        publication['queued_replay']=int((root/'io-jobs/replay.pkl').exists())
        try:
            archive_status=json.loads((root/'archive-status.json').read_text())
            state['backup']='deferred:archive' if archive_status.get('failures') else 'pending' if archive_status.get('pending') or publication['queued_archives'] else 'verified' if list((root/'archive-verified').glob('*.json')) else 'pending'
        except (OSError,ValueError):pass
        if publish:io.start(root)
        reporter.round=state['generation'];reporter.base_steps=sum(m.num_timesteps for m in models)
        reporter(dict(mode_counter_since_generation=state.get('mode_counter_since_generation'),mixed_training_active=kind=='mission',contract=state['contract'],teacher_condition='enhanced' if coach else 'ordinary' if teacher_enabled else 'ppo_only',collected_rounds_by_mode=state.get('collected_rounds_by_mode',{}),completed_by_mode=state.get('completed_by_mode',{}),learning_diagnostics={f'PPO{i+1}':state.get(f'ppo{i+1}_last_update',{}) for i in range(2)},last_completed_evaluation=state.get('last_evaluation'),phase=phase,games=state['completed_games'],sim_seconds=simulated,policy_steps=reporter.base_steps,algorithm='Independent adaptive MaskablePPO',maps='3 balanced modes' if kind=='mission' else '4 terrain variants',nim_in_training=teacher_enabled,teacher=dict(query.stats),coaching=coach.stats if coach else None,learners=[dict(id=f'PPO{i+1}',steps=m.num_timesteps,teacher_samples=len(buffers[i].rows)) for i,m in enumerate(models)],decision_seconds=10,teacher_seconds=30,workers=adaptive.workers,cpu_budget=resources()['cpu_budget'],adaptation_reason=adaptive.reason,aggregate_sim_speed=True,worker_sim_seconds=dict(worker_sim),games_per_hour=(state['completed_games']-completed_start)*3600/elapsed,updates_per_hour=updates*3600/elapsed,evaluation_cases=cases,evaluation_total=240 if kind=='mission' else 80,backup=state.get('backup','pending'),map_id=state['map_id'],map_version=state['map_version'],rules_version=state['rules_version'],runtime_schema='adaptive-1',publication=publication,run_id=state['run'],control_version=control.state().get('version',0)),force=force)
    report.advance_simulation=reporter.advance_simulation
    def checkpoint():
        with reporter.busy():
            if coach:
                coach.close();coach.poll(buffers,[os.getpid(),*[s['worker'].process.pid for s in slots]],True)
            for slot in slots:slot['worker'].call('mark','WAITING')
            all_bundles=[]
            for slot in slots:
                b=slot['worker'].call('snapshot');b['info'].update(active=slot['info']['active'],episode_starts=slot['info'].get('episode_starts',{'A':True,'B':True}));b['actor_rng']=[g.get_state().tolist() for g in slot['generators']];all_bundles.append(b)
            primary=restore(make_env(kind),all_bundles[0]['environment']);primary.accelerated_snapshot=all_bundles
            info=all_bundles[0]['info']
            for k in ('descriptor','assignments','fixed_opponent','initial_frame','metrics','episode_starts','policy_spans'):state[k]=info.get(k)
            state['control_desired']=control.state()['desired']
            state.update(active=info['active'],episode=info.get('episode',next_episode),next_episode=next_episode,adaptive=dict(workers=adaptive.workers,reason=adaptive.reason))
            safe_query=buffer_class();safe_query.stats=dict(query.stats);safe_query.cooldown=query.cooldown
            path=backend.save(root,models,primary,buffers,safe_query,generators,state);backend.record_update(root,state,models)
            if coach:coach.prune()
            return path
    def archive_checkpoint(path,full):
        io.archive(root,path,state,full)
        if not publish:return
        io.start(root)
    try:
        # Preserve source recovery independently of slow remote publication.
        path=checkpoint()
        if not state.get('adaptive_source_pinned'):archive_checkpoint(path,True);state['adaptive_source_pinned']=True
        evaluation_step=96 if kind=='mission' else 50
        # Finish the pre-existing frozen evaluation before collecting new experience.
        if state['completed_games']//evaluation_step>state.get('last_evaluation',0)//evaluation_step:
            milestone=state['completed_games']//evaluation_step*evaluation_step
            evaluation_games=milestone if (root/'evaluations'/f'games-{milestone:08d}'/'report.json').exists() else state['completed_games']
            report('evaluation',True);evaluation.evaluate(root,models,dict(state,completed_games=evaluation_games),report);state['last_evaluation']=milestone;checkpoint()
        if not max_updates:evaluation.ensure_initial_worker(root,state)
        adaptive.resume_measurement()
        while not stopped() and (not max_updates or updates<max_updates):
            if control.paused():
                if coach:coach.poll(buffers,[os.getpid()],True)
                checkpoint();report('paused',True)
                while control.paused() and not stopped():
                    teacher.drain();report('paused');time.sleep(1)
                adaptive.resume_measurement()
                if stopped():break
            if coach:
                coach.schedule(state['completed_games']);coach.poll(buffers,[os.getpid(),*[s['worker'].process.pid for s in slots]],control.paused())
            io.disk_guard(root);teacher.drain();paths=[{},{}];total_rounds=0;batch_sim=0.;evaluated=False
            active=fixed_workers or adaptive.workers
            if coach and coach.running():active=min(active,max(1,int(resources()['cpu_budget'])-2))
            while len(slots)<active:add_slot()
            for index,slot in enumerate(slots):slot['worker'].call('mark','RUNNING' if index<active else 'WAITING')
            while total_rounds<collection_rounds and not stopped() and not control.paused():
                ids=list(range(min(active,collection_rounds-total_rounds)))
                for index in ids:
                    if not slots[index]['info']['active']:begin(index)
                pending=set(ids);before={i:packets[i]['tick'] for i in ids};last={i:{} for i in ids}
                while pending:
                    actions_by_worker={}
                    for index in sorted(pending):
                        slot=slots[index];info=slot['info'];packet=packets[index];actions={}
                        fixed_path=info.get('fixed_opponent');fixed=None
                        if fixed_path:
                            if fixed_path not in fixed_cache:fixed_cache[fixed_path]=backend.CandidatePolicy(root/fixed_path)
                            fixed=fixed_cache[fixed_path]
                        for team in ('A','B'):
                            if packet['finished'][team]:continue
                            learner=info['assignments'][team];x=packet['vectors'][team];mask=packet['masks'][team]
                            if learner in ('PPO1','PPO2'):
                                i=int(learner[-1])-1;action,value,logp=choose(models[i],x,mask,slot['generators'][i]);key=(index,info['episode'],team)
                                row=dict(obs=x,mask=mask,action=action,value=value,logp=logp,reward=0.,terminal=False,advance=False,start=info['episode_starts'][team]);info['episode_starts'][team]=False
                                paths[i].setdefault(key,[]).append(row);last[index][team]=row
                            else:action=fixed.predict(x,mask) if fixed else packet['heuristic'][team]
                            actions[team]=action
                        actions_by_worker[index]=actions;slot['worker'].send('step',(actions,state['generation']))
                    for index in sorted(pending):
                        p=packets[index]=slots[index]['worker'].receive()
                        if p['tick']!=before[index] or p['ended']:
                            for team,row in last[index].items():row.update(reward=float(p['rewards'][team]),terminal=p['ended'],advance=True)
                    pending={i for i in pending if packets[i]['tick']==before[i] and not packets[i]['ended']}
                for index in ids:
                    slot=slots[index];p=packets[index];info=slot['info'];delta=(p['tick']-before[index])*.2;simulated+=delta;batch_sim+=delta;worker_sim[index]+=delta;total_rounds+=1;state['rounds']+=1
                    if p['ended']:
                        b=slot['worker'].call('snapshot');w=b['environment']['world'];meta=b['info'];policy_ids={}
                        for team,learner in info['assignments'].items():
                            if learner in ('PPO1','PPO2'):
                                identity=root/('identity-'+learner+'.npz');backend.export(models[int(learner[-1])-1],identity);policy_ids[team]=backend.CandidatePolicy(identity).policy_id;identity.unlink()
                            else:policy_ids[team]=fixed_cache[info['fixed_opponent']].policy_id if info.get('fixed_opponent') else 'algorithm'
                        metadata=dict(run=state['run'],episode=info['episode'],assignments=info['assignments'],descriptor=info['descriptor'],generation=state['generation'],policy_spans=meta['policy_spans'],metrics=finish(meta['metrics'],w,meta['initial_frame']))
                        from .results import record_world
                        record_world('data/results.sqlite',w,'training',policy_ids,match_id=f'{state["run"]}-{info["episode"]:08d}',initial_frame=meta['initial_frame'],metadata={'league':metadata})
                        for team,learner in info['assignments'].items():
                            if learner in ('PPO1','PPO2'):
                                roles=metadata['metrics']['teams'].get(team,{}).get('selected',{})
                                state.setdefault('behavior_profiles',{})[learner]='|'.join(k for k,v in sorted(roles.items(),key=lambda r:(-r[1],r[0]))[:2]) or 'unknown'
                        state['completed_games']+=1;info['active']=False
                        counts=state.setdefault('completed_by_mode',{});mode=info['descriptor'].get('scenario_id','2');counts[mode]=counts.get(mode,0)+1
                        if publish:
                            engine=restore(make_env(kind),b['environment']).engine
                            io.latest(root,'replay',(engine,meta['initial_frame'],{'league':dict(run=state['run'],assignments=info['assignments'],generation=state['generation'])}))
                for index in ids:
                    state.setdefault('mode_counter_since_generation',state['generation'])
                    counts=state.setdefault('collected_rounds_by_mode',{});mode=slots[index]['info']['descriptor'].get('scenario_id','2');counts[mode]=counts.get(mode,0)+1
                if coach:
                    for index in ids:
                        p=packets[index]
                        if not p['ended'] and p['tick'] and p['tick']%1500==0:
                            bundle=slots[index]['worker'].call('snapshot');world=bundle['environment']['world']
                            recent=world.events[-2000:]
                            reason='supply' if any(ev['event_kind']=='ORDER_FAILED' and ev['payload'].get('reason')=='INSUFFICIENT_SUPPLY' for ev in recent) else 'transport' if any(ev['event_kind']=='ORDER_FAILED' and ev['payload'].get('reason') in ('TRAFFIC_TIMEOUT','FORMATION_UNREACHABLE') for ev in recent) else 'no_progress' if not any(ev['event_kind'] in ('ABSTRACT_ATTACK','FLAG_STOLEN','BUILDING_ENTERED','UNIT_RESUPPLIED') and ev['sim_tick']>world.tick-1500 for ev in recent) else None
                            if reason:coach.failure(world,reason,slots[index]['info']['assignments'])
                eligible=[i for i in ids if not packets[i]['ended'] and packets[i]['tick']%150==0]
                if teacher_enabled and not control.paused() and eligible and time.monotonic()>=max(teacher.next_request,query.cooldown) and teacher.future is None:
                    origin=(teacher.last_worker+1) if teacher.last_worker is not None else 0
                    index=min(eligible,key=lambda i:(i-origin)%len(slots));slot=slots[index]
                    frozen=slot['worker'].call('teacher');teacher.offer(frozen,slot['info']['assignments'],index,state['generation'])
                teacher.drain();report()
            if not total_rounds:
                if control.paused() and not stopped():continue
                break
            # Each trajectory gets its own terminal/bootstrap GAE before flattening.
            teacher.drain()
            for i,model in enumerate(models):
                rows=trajectory_rows(model,paths[i],packets)
                state[f'ppo{i+1}_last_update']=update(model,rows,0.,buffers[i])
                if not exploring:backend.export(model,root/'opponents'/f'ppo{i+1}-{state["generation"]:08d}.npz')
                pinned={s['info'].get('fixed_opponent') for s in slots}
                for old in sorted((root/'opponents').glob(f'ppo{i+1}-*.npz'))[:-8]:
                    if str(old.relative_to(root)) not in pinned:old.unlink()
            state['generation']+=1;updates+=1
            if not fixed_workers:
                reserve=int(not max_updates and not evaluation.initial_complete(root))
                adaptive.observe(batch_sim,reserved=reserve)
            else:adaptive.workers=fixed_workers;adaptive.reason='verification_fixed_workers'
            pinned={s['info'].get('fixed_opponent') for s in slots};fixed_cache={k:v for k,v in fixed_cache.items() if k in pinned}
            # Counters and all environments become durable before remote enqueue.
            path=checkpoint()
            policy_due=state['completed_games']-state['last_policy_archive']>=10 or state['generation']-state.get('last_policy_update',state['generation'])>=24
            full_due=state['completed_games']-state['last_full_archive']>=50 or state['generation']-state.get('last_full_update',state['generation'])>=120
            if policy_due:archive_checkpoint(path,False);state.update(last_policy_archive=state['completed_games']//10*10,last_policy_update=state['generation'])
            if full_due:archive_checkpoint(path,True);state.update(last_full_archive=state['completed_games']//50*50,last_full_update=state['generation'])
            if state['completed_games']//evaluation_step>state.get('last_evaluation',0)//evaluation_step and not stopped():
                evaluated=True;evaluation_games=state['completed_games']
                report('evaluation',True);evaluation.evaluate(root,models,state,report)
                if exploring:
                    from .opponent_population import evaluate_selection
                    evaluate_selection(root,models,state,report,pinned=[Path(s['info']['fixed_opponent']).name for s in slots if s['info'].get('fixed_opponent')])
                state['last_evaluation']=state['completed_games']//evaluation_step*evaluation_step
                if not max_updates and kind=='mission' and evaluation.initial_complete(root):
                    verdict=evaluation.pilot_report(root,state)
                    if verdict['pause']:state['pause_reason']='evaluation_regression';stop['value']=True
            if state['completed_games']>=pilot and not state.get('pilot_report') and not max_updates and not stopped():
                if not evaluation.initial_complete(root):state['pause_reason']='waiting_initial_evaluation';stop['value']=True
                else:
                    verdict=evaluation.pilot_report(root,state);state['pilot_report']=verdict
                    if verdict['pause']:state['pause_reason']='pilot_regression';stop['value']=True
                    elif any(v and v['mean']>0 for v in verdict.get('modes' if kind=='mission' else 'learners',{}).values()):
                        evaluated=True;evaluation.confirm(root,models,state,report)
            if evaluated:checkpoint()
            else:commit_metadata(root,state)
            report('checkpoint_saved',True)
            if evaluated:adaptive.resume_measurement()
    except InterruptedError:pass
    except RuntimeError as exc:
        if str(exc)!='ARCHIVE_DISK_LIMIT':raise
        state['pause_reason']='ARCHIVE_DISK_LIMIT'
    finally:
        teacher.close()
        if coach:
            coach.close();coach.poll(buffers,[os.getpid()],True)
        try:checkpoint()
        finally:
            for slot in slots:slot['worker'].close()
            for sig,handler in old_handlers.items():signal.signal(sig,handler)
            reporter(dict(status='stopped',phase='stopped',games=state['completed_games'],pause_reason=state.get('pause_reason')),force=True)
    return state

if __name__=='__main__':
    import fcntl
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--source',required=True);p.add_argument('--kind',choices=['legacy','mission'],default='legacy');p.add_argument('--pilot',type=int,default=200);p.add_argument('--updates',type=int,default=0);p.add_argument('--no-teacher',action='store_true');p.add_argument('--workers',type=int,choices=(1,2,3));a=p.parse_args()
    root=Path(a.root);root.mkdir(parents=True,exist_ok=True);lock=(root/'runner.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('league worker already running')
    (root/'runner.pid').write_text(str(os.getpid()));run(root,a.source,a.kind,a.pilot,a.updates,not a.no_teacher,fixed_workers=a.workers)
