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


def mixed(spec,paths,content_digest):
    root=Path(paths['validation']);pilot=Path(paths['pilot']);status=read(root/'rollout-status.json');audit=read(root/'engine-audit.json');steps=[]
    rows=audit.get('results',[])
    for mode,name in [('2','고지점령'),('3','섬멸'),('4','깃발전')]:
        cases=[r for r in rows if r.get('scenario_id')==mode];passed=sum(r.get('complete',False) and r.get('replay_hash_verified',False) for r in cases)
        failed=any(r.get('complete') and r.get('replay_hash_verified') is False for r in cases)
        state='FAIL' if failed else 'PASS' if passed==10 else 'RUN' if status.get('stage')=='engine_audit' and status.get('status')=='running' else 'WAIT'
        steps.append(step('engine-'+mode,'맵 '+mode+' '+name+' 엔진 진단',state,passed,10))
    retention=read(root/'migration-retention.json');steps.append(step('retention','기존 맵 2 정책 유지 평가','PASS' if retention.get('complete') and retention.get('retained') else 'FAIL' if retention.get('complete') else 'RUN' if status.get('stage','').startswith('migration_retention') and status.get('status')=='running' else 'WAIT',len(retention.get('results',[])),None))
    state=read(pilot/'state.json');games=state.get('completed_games',0)
    steps.append(step('pilot','격리 혼합 학습 파일럿','PASS' if games>=192 else 'RUN' if state.get('run') else 'WAIT',min(192,games),192))
    latest=read(pilot/'evaluations'/f'games-{games:08d}'/'report.json');initial=read(pilot/'evaluations/games-00000000/report.json');verdict=state.get('pilot_report',{});confirmation=read(pilot/'confirmation-report.json')
    needs_confirmation=any(v.get('mean',0)>0 for v in verdict.get('modes',{}).values())
    fixed_ready=games>=192 and initial.get('complete') and latest.get('complete') and verdict and not verdict.get('pause',True) and (not needs_confirmation or confirmation and not confirmation.get('pause',True))
    steps.append(step('evaluation','模드별 필수 고정·확인 평가'.replace('模','모'),'PASS' if fixed_ready else 'FAIL' if verdict.get('pause') else 'RUN' if latest and not latest.get('complete') else 'WAIT',len(latest.get('results',[])),240))
    current=read(pilot/'current.json');folder=pilot/current.get('path','__missing__');verified=False
    if state and current:
        import hashlib
        policies={f'ppo{i}.npz':hashlib.sha256((folder/f'ppo{i}.npz').read_bytes()).hexdigest() for i in (1,2) if (folder/f'ppo{i}.npz').exists()}
        verified=len(policies)==2 and any((m:=read(p)).get('status')=='verified' and m.get('full') and m.get('generation')==state.get('generation') and m.get('policies')==policies for p in (pilot/'archive-verified').glob('*.json'))
    steps.append(step('recovery','후보 전체 복구본·다운로드·로딩 검증','PASS' if verified else 'WAIT'))
    static=read(root/'validation.json');expected=spec['artifact'].get('runtime_digest');valid=bool(expected and static.get('code_sha256')==expected and static.get('static_checks_passed') and static.get('geometry_complete'))
    steps.append(step('build','코드·지형·필수 결함 검증','PASS' if valid else 'WAIT'))
    blockers=[]
    if status.get('status')=='paused':blockers.append('VALIDATION_PAUSED')
    if state.get('pause_reason'):blockers.append('PILOT_PAUSED')
    current_case=read(root/'audit-current.json');activity=None
    if not current_case:
        for p in Path(paths.get('activity','data/activity')).glob('*.json'):
            item=read(p)
            if item.get('role')=='diagnostic' and item.get('run_id')=='T11' and item.get('process_start')==process_start(item.get('pid',0)) and item.get('state')=='RUNNING' and time.time()-item.get('updated_at',0)<90:
                activity=item;break
        if activity:current_case=dict(phase='simulation',case=activity.get('match_id'),scenario_id=activity.get('scenario_id'),sim_seconds=activity.get('sim_seconds'),updated_at=activity.get('updated_at'))
    return dict(steps=steps,blockers=blockers,current=current_case or None,evidence_digest=content_digest if valid else None,connection='online')


def pages(spec,paths,content_digest):
    proof=read(Path(paths['artifact'])/'validation.json');expected=spec['artifact'].get('sha256')
    checks=[step(k,title,'PASS' if proof.get(k) is True else 'WAIT') for k,title in [('tests','웹 테스트'),('build','고정 배포물 빌드'),('preview','미리보기 검증'),('rollback','이전 배포 복구 확인')]]
    valid=bool(expected and expected==proof.get('artifact_sha256'))
    return dict(steps=checks,blockers=[] if valid else ['ARTIFACT_NOT_VERIFIED'],evidence_digest=content_digest if valid else None,connection='online')


def observe(spec,paths,content_digest):
    if spec.get('planned'):return dict(steps=[step('plan','설계·구현 예정')],blockers=[],connection='online',evidence_digest=None)
    return (mixed if spec['handler']=='mixed_training' else pages)(spec,paths,content_digest)
