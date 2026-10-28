"""Durable typed release registry; observations never grant execution authority."""
import hashlib,json,re,sqlite3,time,uuid
from pathlib import Path
from contextlib import contextmanager

ACTIONS={'apply','set_auto','rollback'}
HANDLERS={'mixed_training','pages_site'}
ID=re.compile(r'^[a-z0-9][a-z0-9-]{0,63}$')


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

class Registry:
    def __init__(self,root):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        with self.db() as c:c.executescript('''
        CREATE TABLE IF NOT EXISTS releases(id TEXT PRIMARY KEY,spec TEXT,digest TEXT,state TEXT,auto INTEGER DEFAULT 0,updated REAL);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,release_id TEXT,at REAL,code TEXT,data TEXT);
        CREATE TABLE IF NOT EXISTS commands(id TEXT PRIMARY KEY,payload TEXT,result TEXT);
        CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,release_id TEXT,digest TEXT,action TEXT,phase TEXT,journal TEXT,updated REAL);
        CREATE TABLE IF NOT EXISTS intents(release_id TEXT PRIMARY KEY,at REAL,id TEXT);
        ''')
    @contextmanager
    def db(self):
        with sqlite3.connect(self.root/'registry.sqlite',timeout=30) as c:
            c.row_factory=sqlite3.Row;c.execute('PRAGMA journal_mode=WAL');yield c
    def event(self,c,id,code,**data):c.execute('INSERT INTO events(release_id,at,code,data) VALUES(?,?,?,?)',(id,time.time(),code,json.dumps(data)))
    def register(self,spec):
        allowed={'id','revision','title','description','targets','dependencies','handler','artifact','validation_plan','planned'}
        if set(spec)-allowed or not ID.fullmatch(spec.get('id','')) or type(spec.get('revision')) is not int or spec['revision']<1 or spec.get('handler') not in HANDLERS:raise ValueError('invalid release manifest')
        if not all(k in spec for k in ('title','description','targets','dependencies','artifact','validation_plan')):raise ValueError('incomplete release manifest')
        if not isinstance(spec['validation_plan'],list) or not spec['validation_plan'] or any(not ID.fullmatch(k) for k in spec['validation_plan']):raise ValueError('required validation plan missing')
        checksum=digest(spec)
        with self.db() as c:
            row=c.execute('SELECT * FROM releases WHERE id=?',(spec['id'],)).fetchone()
            if row and row['digest']==checksum:return checksum
            if row and json.loads(row['spec'])['revision']>=spec['revision']:raise ValueError('content changes require a newer revision')
            if row and json.loads(row['state']).get('status')=='APPLYING':raise ValueError('release currently applying')
            state=dict(status='PLANNED' if spec.get('planned') else 'VALIDATING',steps=[],blockers=[],connection='unknown')
            c.execute('INSERT OR REPLACE INTO releases VALUES(?,?,?,?,?,?)',(spec['id'],json.dumps(spec),checksum,json.dumps(state),0,time.time()))
            self.event(c,spec['id'],'REGISTERED' if not row else 'REVISION_CHANGED',revision=spec['revision'])
        return checksum
    def get(self,id,private=False):
        if not ID.fullmatch(id):raise ValueError('invalid release id')
        with self.db() as c:
            r=c.execute('SELECT * FROM releases WHERE id=?',(id,)).fetchone()
            if not r:raise KeyError(id)
            spec=json.loads(r['spec']);state=json.loads(r['state']);attempts=c.execute('SELECT id,digest,action,phase,updated,journal FROM attempts WHERE release_id=? ORDER BY updated DESC LIMIT 10',(id,)).fetchall()
        public={k:spec[k] for k in ('id','revision','title','description','targets','dependencies','handler')}
        safe_attempts=[]
        for a in attempts:
            entry=dict(a);journal=json.loads(entry.pop('journal'));version=journal.get('old_version')
            if isinstance(version,dict):entry['rollback_target']={k:version.get(k) for k in ('rules_version','contract','generation')}
            if journal.get('old_deployment'):entry['rollback_deployment']=journal['old_deployment']
            safe_attempts.append(entry)
        candidate={k:spec['artifact'].get(k) for k in ('artifact_id','runtime_digest','source_commit','activation')}
        result=dict(**public,candidate=candidate,content_digest=r['digest'],auto_apply=bool(r['auto']),updated_at=r['updated'],**state,attempts=safe_attempts)
        if private:result['spec']=spec
        return result
    def all(self):
        with self.db() as c:ids=[r[0] for r in c.execute('SELECT id FROM releases ORDER BY id')]
        return [self.get(id) for id in ids]
    def observe(self,id,observation):
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE');r=c.execute('SELECT * FROM releases WHERE id=?',(id,)).fetchone();spec=json.loads(r['spec']);previous=json.loads(r['state']);steps=observation.get('steps',[])
            dependencies=[self._dependency(c,d) for d in spec['dependencies']]
            ready=bool(steps) and set(spec['validation_plan']).issubset({s['id'] for s in steps}) and all(s['state']=='PASS' for s in steps if s.get('required',True) or s['id'] in spec['validation_plan']) and all(dependencies) and observation.get('evidence_digest')==r['digest']
            failed=any(s['state']=='FAIL' for s in steps if s.get('required',True) or s['id'] in spec['validation_plan'])
            blockers=list(observation.get('blockers',[]))
            if not all(dependencies):blockers.append('DEPENDENCY_NOT_APPLIED')
            status='PLANNED' if spec.get('planned') else 'READY' if ready and not blockers else 'BLOCKED' if failed or blockers else 'VALIDATING'
            if previous.get('status') in ('APPLYING','APPLIED','ROLLED_BACK'):status=previous['status']
            recovery=c.execute("SELECT 1 FROM attempts WHERE release_id=? AND phase='RECOVERY_REQUIRED'",(id,)).fetchone()
            if recovery:status='BLOCKED';blockers.append('RECOVERY_REQUIRED')
            state=dict(observation,status=status,blockers=blockers)
            if previous.get('status')!=status:self.event(c,id,'STATE_CHANGED',state=status)
            for step in steps:
                old=next((x for x in previous.get('steps',[]) if x['id']==step['id']),{})
                if old.get('state')!=step['state'] or old.get('completed')!=step.get('completed'):self.event(c,id,'CHECK_PROGRESS',step=step['id'],state=step['state'],completed=step.get('completed'),total=step.get('total'))
            if observation.get('invalidated') and r['auto']:
                c.execute('UPDATE releases SET auto=0 WHERE id=?',(id,));self.event(c,id,'AUTO_INVALIDATED')
            c.execute('UPDATE releases SET state=?,updated=? WHERE id=?',(json.dumps(state),time.time(),id))
    def _dependency(self,c,d):
        r=c.execute('SELECT spec,state FROM releases WHERE id=?',(d['id'],)).fetchone()
        return bool(r and json.loads(r['spec'])['revision']==d['revision'] and json.loads(r['state']).get('status')=='APPLIED')
    def command(self,payload,now=None):
        now=time.time() if now is None else now
        keys={'request_id','release_id','content_digest','action','enabled','actor_id','created_at','expires_at'}
        if set(payload)!=keys or payload['actor_id']!='82876856' or payload['action'] not in ACTIONS:raise ValueError('invalid release command')
        try:assert str(uuid.UUID(payload['request_id']))==payload['request_id']
        except (AssertionError,ValueError,TypeError):raise ValueError('invalid request id')
        with self.db() as c:
            old=c.execute('SELECT payload,result FROM commands WHERE id=?',(payload['request_id'],)).fetchone()
            if old:
                if json.loads(old['payload'])!=payload:raise ValueError('request id conflict')
                return json.loads(old['result'])
        if type(payload['created_at']) not in (int,float) or payload['created_at']>now+60:raise ValueError('invalid command time')
        if payload['action']=='set_auto':
            if type(payload['enabled']) is not bool or payload['expires_at'] is not None:raise ValueError('invalid automatic intent')
        elif payload['enabled'] is not None or type(payload['expires_at']) not in (int,float) or not payload['created_at']<=now<payload['expires_at']<=payload['created_at']+600:raise ValueError('expired command')
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE');old=c.execute('SELECT payload,result FROM commands WHERE id=?',(payload['request_id'],)).fetchone()
            if old:
                if json.loads(old['payload'])!=payload:raise ValueError('request id conflict')
                return json.loads(old['result'])
            r=c.execute('SELECT * FROM releases WHERE id=?',(payload['release_id'],)).fetchone()
            if not r or r['digest']!=payload['content_digest']:raise ValueError('stale release revision')
            state=json.loads(r['state']);action=payload['action'];result=dict(request_id=payload['request_id'],status='accepted')
            if action=='set_auto':
                if payload['enabled'] and state['status'] in ('APPLYING','APPLIED','ROLLED_BACK'):raise ValueError('release no longer reservable')
                prior=c.execute('SELECT at,id FROM intents WHERE release_id=?',(r['id'],)).fetchone()
                if prior and (prior['at'],prior['id'])>(payload['created_at'],payload['request_id']):raise ValueError('stale authorization intent')
                c.execute('INSERT OR REPLACE INTO intents VALUES(?,?,?)',(r['id'],payload['created_at'],payload['request_id']))
                c.execute('UPDATE releases SET auto=? WHERE id=?',(int(payload['enabled']),r['id']))
                self.event(c,r['id'],'AUTO_ENABLED' if payload['enabled'] else 'AUTO_DISABLED')
            else:
                if action=='apply' and state['status']!='READY':raise ValueError('release not ready')
                if action=='rollback' and state['status']!='APPLIED':raise ValueError('no applied release to roll back')
                if c.execute("SELECT 1 FROM attempts WHERE phase NOT IN ('APPLIED','FAILED','ROLLED_BACK')").fetchone():raise ValueError('another release is applying')
                attempt=payload['request_id'];c.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?)',(attempt,r['id'],r['digest'],action,'QUEUED','{}',now));result['attempt_id']=attempt
                state['status']='APPLYING';c.execute('UPDATE releases SET state=?,auto=0 WHERE id=?',(json.dumps(state),r['id']));self.event(c,r['id'],'REQUEST_ACCEPTED',action=action,attempt=attempt)
            c.execute('INSERT INTO commands VALUES(?,?,?)',(payload['request_id'],json.dumps(payload),json.dumps(result)))
        return result
    def auto_request(self):
        for r in self.all():
            if r['auto_apply'] and r['status']=='READY' and r.get('connection')=='online':
                now=time.time()
                return self.command(dict(request_id=str(uuid.uuid4()),release_id=r['id'],content_digest=r['content_digest'],action='apply',enabled=None,actor_id='82876856',created_at=now,expires_at=now+600))
    def pending(self):
        with self.db() as c:
            r=c.execute("SELECT * FROM attempts WHERE phase NOT IN ('APPLIED','FAILED','ROLLED_BACK') ORDER BY updated LIMIT 1").fetchone()
            return dict(r) if r else None
    def journal(self,attempt,phase,**values):
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE');r=c.execute('SELECT * FROM attempts WHERE id=?',(attempt,)).fetchone();journal=json.loads(r['journal']);journal.update(values)
            c.execute('UPDATE attempts SET phase=?,journal=?,updated=? WHERE id=?',(phase,json.dumps(journal),time.time(),attempt));self.event(c,r['release_id'],'APPLY_PHASE',phase=phase)
            if phase in ('APPLIED','FAILED','ROLLED_BACK'):
                item=c.execute('SELECT state FROM releases WHERE id=?',(r['release_id'],)).fetchone();state=json.loads(item['state']);state.update(status=phase,latest_attempt=attempt)
                c.execute('UPDATE releases SET state=?,auto=0 WHERE id=?',(json.dumps(state),r['release_id']))
    def events(self,id,after=None,before=None,limit=200):
        if not ID.fullmatch(id) or not 1<=limit<=200:raise ValueError('invalid event query')
        where='release_id=?';args=[id]
        if after is not None:where+=' AND seq>?';args.append(after)
        if before is not None:where+=' AND seq<?';args.append(before)
        with self.db() as c:
            rows=c.execute('SELECT * FROM events WHERE '+where+' ORDER BY seq '+('ASC' if after is not None else 'DESC')+' LIMIT ?',(*args,limit)).fetchall()
        rows=sorted(rows,key=lambda r:r['seq'])
        return [dict(seq=r['seq'],at=r['at'],code=r['code'],data=json.loads(r['data'])) for r in rows]
