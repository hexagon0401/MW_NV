"""Local durable PPO-only desired state. Remote commands never supply executable args."""
import json,os,sqlite3,time,uuid
from pathlib import Path
from .telemetry import atomic,process_start

ACTIONS={'pause_ppo':'paused','resume_ppo':'running'}
def directory():
    value=os.environ.get('MW_NV_CONTROL_ROOT');return Path(value) if value else None

def state(root=None):
    root=Path(root) if root else directory()
    if root is None:return dict(desired='running',version=0,enabled=False)
    try:return json.loads((root/'state.json').read_text())
    except FileNotFoundError:return dict(desired='running',version=0,enabled=True)
    except (OSError,ValueError):return dict(desired='paused',version=0,enabled=True,error='invalid_control_state')
def paused():return state()['desired']=='paused'

def register(run_root,source,kind,pilot,run_id,restored_desired=None):
    root=directory()
    if root is None:return
    root.mkdir(parents=True,exist_ok=True)
    if not (root/'state.json').exists():atomic(root/'state.json',dict(desired=restored_desired or 'running',version=0,enabled=True))
    if restored_desired=='paused' and (root/'control.sqlite').exists():
        with sqlite3.connect(root/'control.sqlite') as conn:
            row=conn.execute('SELECT version FROM desired WHERE id=1').fetchone()
            if row and row[0]==0:
                conn.execute("UPDATE desired SET mode='paused' WHERE id=1");current=state(root);atomic(root/'state.json',dict(current,desired='paused'))
    atomic(root/'run.json',dict(registered_at=time.time(),root=str(Path(run_root).resolve()),source=str(Path(source).resolve()),kind=kind,pilot=pilot,run_id=run_id,pid=os.getpid(),process_start=process_start(os.getpid())))

def initialize(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(root/'control.sqlite') as conn:
        conn.executescript('CREATE TABLE IF NOT EXISTS desired(id INTEGER PRIMARY KEY,mode TEXT,version INTEGER,instance TEXT); CREATE TABLE IF NOT EXISTS commands(id TEXT PRIMARY KEY,payload TEXT,ack TEXT);')
        row=conn.execute('SELECT mode,version,instance FROM desired WHERE id=1').fetchone()
        if row is None:
            initial=state(root);row=(initial['desired'],initial['version'],str(uuid.uuid4()));conn.execute('INSERT INTO desired VALUES(1,?,?,?)',row)
    atomic(root/'state.json',dict(desired=row[0],version=row[1],instance_id=row[2],enabled=True));return dict(desired=row[0],version=row[1],instance_id=row[2])

def apply(root,command,run_id,now=None):
    root=Path(root);now=time.time() if now is None else now;initialize(root)
    stable=('request_id','action','actor_id','instance_id','run_id','expected_version')
    with sqlite3.connect(root/'control.sqlite') as conn:
        conn.execute('BEGIN IMMEDIATE')
        mode,version,instance=conn.execute('SELECT mode,version,instance FROM desired WHERE id=1').fetchone()
        request_id=command.get('request_id');reason=None
        try:assert str(uuid.UUID(request_id))==request_id
        except (ValueError,TypeError,AttributeError,AssertionError):return dict(status='rejected',reason='invalid_id')
        old=conn.execute('SELECT payload,ack FROM commands WHERE id=?',(request_id,)).fetchone()
        if old:
            original=json.loads(old[0])
            if any(original.get(k)!=command.get(k) for k in stable):return dict(status='rejected',reason='id_conflict')
            return json.loads(old[1])
        allowed=set(stable)|{'created_at','expires_at'}
        if set(command)!=allowed or command.get('action') not in ACTIONS:reason='invalid_command'
        elif command.get('actor_id')!='82876856':reason='not_admin'
        elif command.get('instance_id')!=instance or command.get('run_id')!=run_id:reason='stale_runner'
        elif type(command.get('expected_version'))is not int or command['expected_version']!=version:reason='stale_version'
        elif any(type(command.get(k)) not in (int,float) for k in ('created_at','expires_at')):reason='invalid_time'
        elif not (now-600<=command['created_at']<=now+60 and now<command['expires_at']<=command['created_at']+600):reason='expired'
        if not reason:
            mode=ACTIONS[command['action']];version+=1;conn.execute('UPDATE desired SET mode=?,version=? WHERE id=1',(mode,version))
        ack=dict(**{k:command.get(k) for k in stable},status='rejected' if reason else 'accepted',reason=reason,desired=mode,version=version,at=now)
        conn.execute('INSERT INTO commands VALUES(?,?,?)',(request_id,json.dumps(command),json.dumps(ack)))
    atomic(root/'state.json',dict(desired=mode,version=version,instance_id=instance,enabled=True));return ack

def status(root,training,now=None):
    root=Path(root);now=time.time() if now is None else now;s=initialize(root)
    try:run=json.loads((root/'run.json').read_text())
    except (OSError,ValueError):run={}
    alive=bool(run.get('pid') and process_start(run['pid'])==run.get('process_start') and run.get('process_start') is not None)
    observed='offline' if not alive else 'paused' if training.get('phase')=='paused' and training.get('run_id')==run.get('run_id') and training.get('control_version')==s['version'] else 'saving' if s['desired']=='paused' else 'running'
    with sqlite3.connect(root/'control.sqlite') as conn:recent=[json.loads(row[0]) for row in conn.execute('SELECT ack FROM commands ORDER BY rowid DESC LIMIT 10')]
    for ack in recent:
        if ack['status']=='accepted' and ((ack['desired']=='paused' and observed=='paused') or (ack['desired']=='running' and observed=='running')):ack['status']='applied'
    return dict(**s,run_id=run.get('run_id'),online=True,observed=observed,last_seen=now,recent=recent,learner_alive=alive)

def resume_if_needed(root,base):
    """A resume command can restart a registered, locally recoverable runner only."""
    import subprocess,sys
    root=Path(root);s=state(root)
    if s['desired']!='running':return
    spec=json.loads((root/'run.json').read_text());base=Path(base).resolve();allowed={base/'data/league-v1',base/'data/multi-mode-v1'};run_root=Path(spec['root']).resolve();source=Path(spec['source']).resolve()
    if run_root not in allowed or not source.is_relative_to(base/'data') or spec['kind'] not in ('legacy','mission') or type(spec['pilot'])is not int or not 1<=spec['pilot']<=100000:raise ValueError('unregistered runner')
    if process_start(spec['pid'])==spec.get('process_start') and spec.get('process_start') is not None:return
    try:
        live_pid=int((run_root/'runner.pid').read_text());args=Path(f'/proc/{live_pid}/cmdline').read_bytes().split(b'\0')
        if b'learning.accelerated_league' in args:return
    except (OSError,ValueError):pass
    if (run_root/'STOP').exists():raise ValueError('runner blocked by validation/stop marker')
    if not (run_root/'current.json').exists():raise ValueError('local recovery required')
    with (run_root/'adaptive.log').open('ab') as log:
        subprocess.Popen([sys.executable,'-u','-m','learning.accelerated_league','--kind',spec['kind'],'--root',str(run_root),'--source',str(source),'--pilot',str(spec['pilot'])],cwd=base,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
