"""Incremental local dashboard materializations and bounded immutable Storage pages."""
import collections,gzip,hashlib,itertools,json,sqlite3,time
from datetime import datetime,timezone
from pathlib import Path
from .telemetry import atomic

RANGES={'24h':86400,'7d':604800,'30d':2592000,'all':None}
SCHEMA='''CREATE TABLE IF NOT EXISTS dash_meta(key TEXT PRIMARY KEY,value INTEGER);
CREATE TABLE IF NOT EXISTS dash_matches(id TEXT PRIMARY KEY,at REAL,payload TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS dash_matches_at ON dash_matches(at);
CREATE TABLE IF NOT EXISTS dash_updates(id TEXT PRIMARY KEY,at REAL,run TEXT,learner TEXT,steps INTEGER);
CREATE TABLE IF NOT EXISTS dash_samples(at INTEGER PRIMARY KEY,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS dash_hours(hour INTEGER PRIMARY KEY,payload TEXT NOT NULL);
'''
def connect(db):
    conn=sqlite3.connect(db,timeout=10);conn.executescript(SCHEMA);return conn

def ingest(db):
    with connect(db) as conn:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='records'").fetchone():return 0
        row=conn.execute("SELECT value FROM dash_meta WHERE key='watermark'").fetchone();last=row[0] if row else 0;added=0
        batch=conn.execute('SELECT rowid,kind,payload FROM records WHERE rowid>? ORDER BY rowid',(last,)).fetchall()
        for rid,kind,body in batch:
            r=json.loads(body)
            if kind=='match' and r.get('ended'):
                try:at=datetime.fromisoformat(r['created_at']).timestamp()
                except (ValueError,KeyError,TypeError):at=None
                conn.execute('INSERT OR IGNORE INTO dash_matches VALUES (?,?,?)',(r['id'],at,body));added+=1
            elif kind=='training':
                try:at=datetime.fromisoformat(r['created_at']).timestamp()
                except (ValueError,KeyError,TypeError):at=None
                league=r.get('league',{});conn.execute('INSERT OR IGNORE INTO dash_updates VALUES (?,?,?,?,?)',(r['id'],at,league.get('run'),league.get('learner'),r['steps']))
        if batch:conn.execute("INSERT OR REPLACE INTO dash_meta VALUES ('watermark',?)",(batch[-1][0],))
        return added

def sample(db,doc,at=None):
    stamp=int(time.time() if at is None else at);hour=stamp//3600*3600
    fields={k:v for k,v in doc.items() if isinstance(v,(int,float)) and not isinstance(v,bool)}
    with connect(db) as conn:
        if conn.execute('SELECT 1 FROM dash_samples WHERE at=?',(stamp,)).fetchone():return
        conn.execute('INSERT INTO dash_samples VALUES (?,?)',(stamp,json.dumps(doc)))
        row=conn.execute('SELECT payload FROM dash_hours WHERE hour=?',(hour,)).fetchone();agg=json.loads(row[0]) if row else {}
        for k,v in fields.items():
            a=agg.setdefault(k,dict(sum=0.,n=0,min=v,max=v));a.update(sum=a['sum']+v,n=a['n']+1,min=min(a['min'],v),max=max(a['max'],v))
        conn.execute('INSERT OR REPLACE INTO dash_hours VALUES (?,?)',(hour,json.dumps(agg)))
        conn.execute('DELETE FROM dash_samples WHERE at<?',(stamp-7*86400,));conn.execute('DELETE FROM dash_hours WHERE hour<?',(stamp-90*86400,))

def compact(r):return {k:r.get(k) for k in ('id','created_at','winner','scores','mode','scenario_id','game_mode','policies','rules_version','map_id','map_version')}|dict(assignments=r.get('league',{}).get('assignments',{}))
def scope_key(kind='all',scenario='all',learner='all'):return ':'.join((kind,scenario,learner))
def group_matches(rows):
    groups=collections.defaultdict(list)
    for r in rows:
        learners={v for v in r.get('league',{}).get('assignments',{}).values() if v in ('PPO1','PPO2')}
        for kind,scenario,learner in itertools.product({'all',r['mode']},{'all',str(r.get('scenario_id'))}, {'all',*learners}):groups[scope_key(kind,scenario,learner)].append(r)
    return groups

def reduce_points(points,limit=240):
    if len(points)<=limit:return points
    # Consecutive aggregate buckets: missing values remain missing; expose ranges.
    result=[]
    for i in range(limit):
        group=points[i*len(points)//limit:(i+1)*len(points)//limit];keys={k for p in group for k,v in p.items() if isinstance(v,(int,float))};row=dict(label=group[-1].get('label'),at=group[-1].get('at'),samples=len(group))
        for key in keys:
            values=[p[key] for p in group if isinstance(p.get(key),(int,float))]
            row[key]=sum(values)/len(values);row[key+'_min']=min(values);row[key+'_max']=max(values)
        result.append(row)
    return result

def trends(rows):
    learners={};learning=[];evaluation=[];tactics=[];rolling={x:collections.deque(maxlen=50) for x in ('PPO1','PPO2')};periods={}
    for r in rows:
        assignments=r.get('league',{}).get('assignments',{})
        for team,model in assignments.items():
            if model not in rolling:continue
            i=('A','B').index(team);win=int(r['winner']==i);score=.5 if r['winner'] is None else float(win)
            if r['mode']=='training':
                rolling[model].append(win);l=learners.setdefault(model,dict(games=0,opportunities={},selected={},outcomes={},steps=None));l['games']+=1
                metrics=r.get('league',{}).get('metrics',{}).get('teams',{}).get(team,{})
                for name in ('opportunities','selected'):
                    for key,n in metrics.get(name,{}).items():l[name][key]=l[name].get(key,0)+n
                for key,outcomes in metrics.get('role_outcomes',{}).items():
                    dest=l['outcomes'].setdefault(key,{})
                    for status,n in outcomes.items():dest[status]=dest.get(status,0)+n
            elif r['mode']=='evaluation' and 'initial' in assignments.values():
                milestone=r.get('league',{}).get('evaluation_games')
                if milestone is not None:
                    key=(milestone,str(r.get('scenario_id')));periods.setdefault(key,{x:[] for x in rolling})[model].append(score)
        if r['mode']=='training':
            label=r.get('created_at') or r['id'];learning.append(dict(label=label,**{x.lower():sum(rolling[x])*100/len(rolling[x]) if rolling[x] else None for x in rolling}))
            point=dict(label=label)
            for model,l in learners.items():
                for role,n in l['opportunities'].items():point[model+'_'+role]=100*l['selected'].get(role,0)/n if n else None
            tactics.append(point)
    for (milestone,scenario),scores in sorted(periods.items()):
        evaluation.append(dict(label=f'{milestone}games / map{scenario}',**{x.lower():sum(scores[x])/len(scores[x]) if scores[x] else None for x in rolling}))
    return dict(learning=reduce_points(learning),evaluation=reduce_points(evaluation),tactics=reduce_points(tactics),learners=learners)


def analysis(rows):
    from learning.objective_stats import report,document
    d=report(document(rows));points=[]
    for key,p in d.get('points',{}).items():
        for team,s in p.get('first',{}).items():points.append(dict(name=d['objective_names'].get(key,key),team=team,**s))
    patterns={}
    for r in rows:
        for name,v in r.get('league',{}).get('metrics',{}).get('sequences',{}).get('patterns',{}).items():
            dest=patterns.setdefault(name,{k:0 for k in ('opportunities','success','failed','censored','unknown')})
            for key in dest:dest[key]+=v.get(key,0)
    return dict(coverage=d.get('coverage',{}),points=points,patterns=patterns)

def files(db,snapshot,now=None):
    now=time.time() if now is None else now;updated=datetime.fromtimestamp(now,timezone.utc).isoformat();ingest(db)
    with connect(db) as conn:
        rows=[json.loads(r[0]) for r in conn.execute('SELECT payload FROM dash_matches ORDER BY at,id')]
        updates=conn.execute('SELECT at,run,learner,steps FROM dash_updates ORDER BY at,id').fetchall()
        samples=[dict(json.loads(body),at=stamp,label=datetime.fromtimestamp(stamp,timezone.utc).isoformat()) for stamp,body in conn.execute('SELECT at,payload FROM dash_samples ORDER BY at')]
        hours=[dict({k:v['sum']/v['n'] for k,v in json.loads(body).items() if v['n']},at=stamp,label=datetime.fromtimestamp(stamp,timezone.utc).isoformat()) for stamp,body in conn.execute('SELECT hour,payload FROM dash_hours ORDER BY hour')]
    out={};manifest=dict(updated_at=updated,views={})
    current=dict(snapshot)
    # Resource heartbeat belongs to the collector, not a paused learner.
    current.setdefault('training',{});out['latest.json']=current
    for range_name,seconds in RANGES.items():
        selected=[r for r in rows if seconds is None or (r.get('created_at') and datetime.fromisoformat(r['created_at']).timestamp()>=now-seconds)]
        groups=group_matches(selected)
        for scope,items in groups.items():
            prefix=range_name+':'+scope;entries=[]
            compact_rows=[compact(r) for r in items]
            for offset in range(0,len(compact_rows),100):
                data=compact_rows[offset:offset+100];body=json.dumps(data,separators=(',',':')).encode();key='pages/'+hashlib.sha256(body).hexdigest()[:24]+'.json';out[key]=data;entries.append(key)
            recent=[r for r in items if r['mode'] not in ('demonstration','failure_replay')][-50:];stats=dict(training_games=sum(r['mode']=='training' for r in items),recent_games=len(recent),recent_a_wins=sum(r['winner']==0 for r in recent))
            run_id=snapshot.get('training',{}).get('run_id');rules=snapshot.get('training',{}).get('rules_version')
            learning_rows=[r for r in items if run_id and r.get('league',{}).get('run')==run_id and r['rules_version']==rules]
            learned=trends(learning_rows)
            totals={x:0 for x in ('PPO1','PPO2')};update_points=[]
            for at,run,learner,steps in updates:
                if run!=run_id or learner not in totals:continue
                totals[learner]+=steps
                if at is not None and (seconds is None or at>=now-seconds):update_points.append(dict(label=datetime.fromtimestamp(at,timezone.utc).isoformat(),ppo1=totals['PPO1'],ppo2=totals['PPO2']))
            learned['updates']=reduce_points(update_points)
            for live in snapshot.get('training',{}).get('learners',[]):
                if live['id'] in learned['learners']:learned['learners'][live['id']]['steps']=live.get('steps')
            document=dict(summary=stats,recent=[compact(r) for r in reversed(items[-10:])],**learned,learning_scope=dict(run_id=run_id,rules_version=rules),analysis=analysis(items))
            key='views/'+hashlib.sha256(json.dumps(document,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:24]+'.json';out[key]=document
            manifest['views'][prefix]=dict(total=len(items),pages=entries,document=key)
        source=samples if range_name in ('24h','7d') else hours
        chosen=[p for p in source if seconds is None or p['at']>=now-seconds]
        out['resources-'+range_name+'.json']=dict(updated_at=snapshot.get('updated_at'),current=snapshot.get('resources',{}),points=reduce_points(chosen))
    revision=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest();manifest['revision']=revision
    out['indexes/'+revision+'.json']=manifest
    out['index.json']=manifest
    return out

def publish(db,snapshot,store,root='data/dashboard-cache'):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);out=files(db,snapshot);cache_path=root/'published.json'
    try:cache=json.loads(cache_path.read_text())
    except (OSError,ValueError):cache={}
    retained=cache.get('retained',{});hashes={};now=time.time()
    for key,doc in sorted(out.items(),key=lambda item:item[0] in ('index.json','latest.json')):
        body=gzip.compress(json.dumps(doc,separators=(',',':'),allow_nan=False).encode(),mtime=0);digest=hashlib.sha256(body).hexdigest();hashes[key]=digest
        if retained.get(key,{}).get('sha256')!=digest:store._request('object/'+store.bucket+'/dashboard/'+key+'.gz','PUT',body)
        retained[key]=dict(sha256=digest,last_referenced=now)
    protected=set(hashes)|set(cache.get('current',{}))
    obsolete=[k for k,v in retained.items() if k not in protected and now-v['last_referenced']>=600]
    if obsolete:store._request('object/'+store.bucket,'DELETE',json.dumps(dict(prefixes=['dashboard/'+k+'.gz' for k in obsolete])).encode())
    for k in obsolete:retained.pop(k,None)
    atomic(cache_path,dict(current=hashes,retained=retained))
    return len(out)
