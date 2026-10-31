"""Verified immutable latest replay publication; old readers retain a grace period."""
import gzip,json,hashlib,os,time,fcntl
from pathlib import Path
from engine.viewer_export import export_view
from cloud.supabase_storage import PrivateStorage

def publish_latest(engine,initial,metadata=None):
    Path('data').mkdir(exist_ok=True)
    with Path('data/replay-publication.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        return _publish(engine,initial,metadata)

def _publish(engine,initial,metadata=None):
    doc=export_view(engine,initial);now=time.time();completed_at=(metadata or {}).get('completed_at',now)
    if metadata and metadata.get('league'):
        doc['league']=metadata['league'];doc['initial']['learner_assignments']=dict(metadata['league']['assignments'])
    body=gzip.compress(json.dumps(doc,separators=(',',':')).encode(),mtime=0);digest=hashlib.sha256(body).hexdigest()
    store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY']);prefix='object/authenticated/'+store.bucket+'/'
    entries=json.loads(store._request(prefix+'index.json'));previous=next((e for e in entries if e['id']=='training-latest'),None)
    if previous and previous.get('completed_at',0)>completed_at:return False
    key='training-replays/'+digest+'.view.json.gz'
    store._request('object/'+store.bucket+'/'+key,'PUT',body)
    if hashlib.sha256(store._request(prefix+key)).hexdigest()!=digest:raise ValueError('replay checksum')
    entry=dict(id='training-latest',scores=doc['summary']['scores'],winner=doc['summary']['winner'],policy_version=doc['rules_version'],replay_uri='supabase://'+store.bucket+'/'+key,sha256=digest,mode='training',completed_at=completed_at)
    # Keep exactly three distinct training replays. Historical IDs never change meaning.
    recent=[];seen={digest}
    for old in entries:
        if not (old['id']=='training-latest' or old['id'].startswith('training-replay-')):continue
        sha=old.get('sha256')
        if not sha or sha in seen:continue
        recent.append(dict(old,id='training-replay-'+sha[:24]));seen.add(sha)
        if len(recent)==2:break
    others=[e for e in entries if e['id']!='training-latest' and not e['id'].startswith('training-replay-')][:17]
    published=[entry]+recent+others
    store._request('object/'+store.bucket+'/index.json','PUT',json.dumps(published).encode())
    try:history=json.loads(store._request(prefix+'training-replay-retention.json'))
    except OSError:history=[]
    if previous:
        old_key=previous['replay_uri'].split(store.bucket+'/',1)[1]
        if not any(e['key']==old_key for e in history):history.append(dict(key=old_key,published_at=now))
    history=[e for e in history if e['key']!=key]+[dict(key=key,published_at=now)]
    protected={e['key'] for e in history[-3:]}|{e['replay_uri'].split(store.bucket+'/',1)[1] for e in published if e.get('replay_uri','').startswith('supabase://'+store.bucket+'/')}
    for item in history:
        if item['key'] in protected:item.pop('retired_at',None)
        else:item.setdefault('retired_at',now)
    obsolete=[e['key'] for e in history if e['key'] not in protected and now-e['retired_at']>=600]
    if obsolete:store._request('object/'+store.bucket,'DELETE',json.dumps(dict(prefixes=obsolete)).encode())
    history=[e for e in history if e['key'] not in obsolete]
    store._request('object/'+store.bucket+'/training-replay-retention.json','PUT',json.dumps(history).encode())
    return True
