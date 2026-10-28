"""Read-only adapters for actual diagnostic evidence; missing evidence stays WAIT."""
import json,time
from pathlib import Path
from .telemetry import process_start


_CACHE={}
def read(path):
    try:
        path=Path(path);stat=path.stat();key=str(path);stamp=(stat.st_mtime_ns,stat.st_size)
        if key in _CACHE and _CACHE[key][0]==stamp:return _CACHE[key][1]
        data=json.loads(path.read_text());_CACHE[key]=(stamp,data)
        if len(_CACHE)>128:_CACHE.pop(next(iter(_CACHE)))
        return data
    except (OSError,ValueError):return {}


def step(id,title,state='WAIT',completed=None,total=None):return dict(id=id,title=title,state=state,completed=completed,total=total,required=True)


def worker_alive(info,module):
    try:
        pid=info['pid']
        return process_start(pid)==info.get('start') and module.encode() in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    except (OSError,KeyError):return False

def mixed(spec,paths,content_digest):
    root=Path(paths['validation']);pilot=Path(paths['pilot']);status=read(root/'rollout-status.json');audit=read(root/'engine-audit.json');steps=[]
    source_pilot=pilot;canary=spec['artifact'].get('activation')=='canary'
    active=read(paths['active']) if paths.get('active') else {}
    if canary and active.get('release_id')==spec['id'] and active.get('revision')==spec['revision']:pilot=Path(active['root'])
    rows=audit.get('results',[]);validation_alive=worker_alive(read(root/'validation-agent.json'),'learning.mission_pipeline')
    for mode,name in [('2','고지점령'),('3','섬멸'),('4','깃발전')]:
        cases=[r for r in rows if r.get('scenario_id')==mode];passed=sum(r.get('complete',False) and r.get('replay_hash_verified',False) for r in cases)
        failed=any(r.get('complete') and r.get('replay_hash_verified') is False for r in cases)
        state='FAIL' if failed else 'PASS' if passed==10 else 'RUN' if status.get('stage')=='engine_audit' and status.get('status')=='running' and validation_alive else 'WAIT'
        steps.append(step('engine-'+mode,'맵 '+mode+' '+name+' 엔진 진단',state,passed,10))
    retention=read(root/'migration-retention.json');retention_total=400 if status.get('stage')=='migration_retention_confirmation' or len({r['seed'] for r in retention.get('results',[])})>5 else 80
    retention_done=retention.get('complete') and len(retention.get('results',[]))==retention_total
    steps.append(step('retention','기존 맵 2 정책 유지 평가','PASS' if retention_done and retention.get('retained') else 'FAIL' if retention_done else 'RUN' if status.get('stage','').startswith('migration_retention') and status.get('status')=='running' and validation_alive else 'WAIT',len(retention.get('results',[])),retention_total))
    state=read(pilot/'state.json');games=state.get('completed_games',0);pilot_alive=worker_alive(read(pilot/'child.json'),'learning.accelerated_league')
    if canary and active.get('root')==str(pilot):
        try:
            pid=int((pilot/'runner.pid').read_text());pilot_alive=worker_alive(dict(pid=pid,start=process_start(pid)),'learning.accelerated_league')
        except (OSError,ValueError):pass
    steps.append(step('pilot','격리 혼합 학습 파일럿','PASS' if games>=192 else 'RUN' if pilot_alive else 'WAIT',min(192,games),192))
    evaluation_games=state.get('last_evaluation',games) if canary else games
    latest=read(pilot/'evaluations'/f'games-{evaluation_games:08d}'/'report.json');initial=read(pilot/'evaluations/games-00000000/report.json');verdict=state.get('pilot_report',{});confirmation=read(pilot/'confirmation-report.json')
    needs_confirmation=any(v.get('mean',0)>0 for v in verdict.get('modes',{}).values())
    fixed_ready=games>=192 and initial.get('complete') and latest.get('complete') and verdict and not verdict.get('pause',True) and (not needs_confirmation or confirmation and not confirmation.get('pause',True))
    steps.append(step('evaluation','모드별 필수 고정·확인 평가','PASS' if fixed_ready else 'FAIL' if verdict.get('pause') else 'RUN' if pilot_alive and latest and not latest.get('complete') else 'WAIT',len(latest.get('results',[])),240))
    current=read(source_pilot/'current.json');folder=source_pilot/current.get('path','__missing__');verified=False
    source_state=read(source_pilot/'state.json')
    if source_state and current:
        import hashlib
        policies={f'ppo{i}.npz':hashlib.sha256((folder/f'ppo{i}.npz').read_bytes()).hexdigest() for i in (1,2) if (folder/f'ppo{i}.npz').exists()}
        verified=len(policies)==2 and any((m:=read(p)).get('status')=='verified' and m.get('full') and m.get('generation')==source_state.get('generation') and m.get('policies')==policies for p in (source_pilot/'archive-verified').glob('*.json'))
    steps.append(step('recovery','후보 전체 복구본·다운로드·로딩 검증','PASS' if verified else 'WAIT'))
    static=read(root/'validation.json');expected=spec['artifact'].get('runtime_digest');valid=bool(expected and static.get('code_sha256')==expected and static.get('static_checks_passed') and static.get('geometry_complete'))
    import hashlib
    source_checks=spec['artifact'].get('policy_sources',{})
    assets_valid=bool(source_checks) and all((root/name).is_file() and hashlib.sha256((root/name).read_bytes()).hexdigest()==sha for name,sha in source_checks.items())
    valid=valid and assets_valid
    runtime_valid=False;runtime_changed=False
    if paths.get('runtime') and (Path(paths['runtime'])/'artifact-files.json').exists():
        try:
            from .release_artifacts import verify
            runtime_valid=verify(paths['runtime'],expected)
        except (OSError,ValueError,KeyError):runtime_changed=True
    valid=valid and runtime_valid
    steps.append(step('build','코드·지형·필수 결함 검증','PASS' if valid else 'WAIT'))
    if canary:
        for s in steps:
            if s['id'] in ('retention','pilot','evaluation'):s['required']=False
    blockers=[]
    if runtime_changed:blockers.append('RUNTIME_ARTIFACT_CHANGED')
    if source_checks and not assets_valid:blockers.append('SOURCE_ARTIFACT_CHANGED')
    if status.get('status')=='paused':blockers.append('VALIDATION_PAUSED')
    if state.get('pause_reason'):blockers.append('PILOT_PAUSED')
    current_case=read(root/'audit-current.json');activity=None
    if current_case.get('state')!='RUNNING' or not validation_alive:current_case={}
    if not current_case:
        for p in Path(paths.get('activity','data/activity')).glob('*.json'):
            item=read(p)
            if item.get('role')=='diagnostic' and item.get('run_id')=='T11' and item.get('process_start')==process_start(item.get('pid',0)) and item.get('state')=='RUNNING' and time.time()-item.get('updated_at',0)<90:
                activity=item;break
        if activity:current_case=dict(phase='simulation',case=activity.get('match_id'),scenario_id=activity.get('scenario_id'),sim_seconds=activity.get('sim_seconds'),updated_at=activity.get('updated_at'))
    if state.get('run') and games<192:
        training=read(pilot/'training-status.json');current_case=dict(phase='pilot_evaluation' if training.get('phase')=='evaluation' else 'pilot',case=state.get('episode'),completed_games=games,updated_at=training.get('updated_at'))
    pilot_status=read(pilot/'pilot-status.json')
    if pilot_status.get('status')=='WAITING_RESOURCES' or (pilot/'resource-pause.json').exists():current_case=dict(phase='resource_wait',state='WAITING_RESOURCES')
    current_case={k:v for k,v in current_case.items() if k in ('phase','case','scenario_id','seed','swapped','sim_seconds','time_limit_seconds','state','journal_completed','journal_total','completed_games','updated_at')}
    parallel=read(root/'audit-parallel.json')
    cases=[{k:v for k,v in row.items() if k in ('case','phase','sim_seconds','state','journal_completed','journal_total')} for row in parallel.get('cases',[]) if row.get('state')=='RUNNING'] if validation_alive else []
    return dict(steps=steps,blockers=blockers,current=current_case or None,parallel_cases=cases,release_profile='canary' if canary else 'full',evidence_digest=content_digest if valid else None,connection='online',validation_connection='idle' if status.get('status')=='validated' else 'online' if validation_alive else 'offline',invalidated=bool(runtime_changed or source_checks and not assets_valid))


def pages(spec,paths,content_digest):
    proof=read(Path(paths['artifact'])/'validation.json');expected=spec['artifact'].get('sha256')
    checks=[step(k,title,'PASS' if proof.get(k) is True else 'WAIT') for k,title in [('tests','웹 테스트'),('build','고정 배포물 빌드'),('preview','미리보기 검증'),('rollback','이전 배포 복구 확인')]]
    valid=bool(expected and expected==proof.get('artifact_sha256'))
    return dict(steps=checks,blockers=[] if valid else ['ARTIFACT_NOT_VERIFIED'],evidence_digest=content_digest if valid else None,connection='online')


def observe(spec,paths,content_digest):
    if spec.get('planned'):return dict(steps=[step('plan','설계·구현 예정')],blockers=[],connection='online',evidence_digest=None)
    return (mixed if spec['handler']=='mixed_training' else pages)(spec,paths,content_digest)
