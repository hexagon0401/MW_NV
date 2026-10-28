"""One recovery attempt for a stopped canary, then audited rollback if it fails."""
import json,time,uuid
from pathlib import Path
from .release_observations import read,worker_alive
from .telemetry import atomic,process_start


def monitor(registry,base,now=None):
    now=time.time() if now is None else now;base=Path(base);active=read(registry.root/'active.json')
    if not active:return
    item=registry.get(active['release_id'],private=True)
    if item['status']!='APPLIED' or item['spec']['artifact'].get('activation')!='canary':return
    root=Path(active['root']);path=registry.root/'canary-health.json';health=read(path)
    if health.get('root')!=str(root):health=dict(root=str(root),attempted_resume=False)
    try:
        pid=int((root/'runner.pid').read_text());alive=worker_alive(dict(pid=pid,start=process_start(pid)),'learning.accelerated_league')
    except (OSError,ValueError):alive=False
    state=read(root/'state.json');control=read(base/'data/control/state.json')
    if alive:health.pop('failed_since',None);atomic(path,health);return
    if control.get('desired')=='paused' or (root/'STOP').exists():return
    health.setdefault('failed_since',now)
    if now-health['failed_since']<30:atomic(path,health);return
    if not health['attempted_resume'] and state.get('pause_reason') not in ('evaluation_regression','pilot_regression','ARCHIVE_DISK_LIMIT'):
        health.update(attempted_resume=True,failed_since=now);atomic(path,health)
        from .ppo_control import resume_if_needed
        try:resume_if_needed(base/'data/control',base)
        except (OSError,ValueError):pass
        return
    if now-health['failed_since']<180:return
    with registry.db() as c:registry.event(c,item['id'],'CANARY_RECOVERY_REQUIRED',reason=state.get('pause_reason') if state.get('pause_reason') in ('evaluation_regression','pilot_regression','ARCHIVE_DISK_LIMIT') else 'COORDINATOR_EXITED')
    registry.command(dict(request_id=str(uuid.uuid4()),release_id=item['id'],content_digest=item['content_digest'],action='rollback',enabled=None,actor_id='82876856',created_at=now,expires_at=now+600),now=now)
