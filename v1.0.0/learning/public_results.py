"""Completed results only: no replay expansion, no credentials or host paths."""
import gzip,json,os
from datetime import datetime,timezone
from .results import records

def document(db='data/results.sqlite'):
    rows=[r for r in records(db,kind='match') if r['kind']=='match' and r.get('ended')]
    rows.sort(key=lambda r:(r.get('created_at',''),r['id']),reverse=True)
    teams={a:dict(wins=0,losses=0,draws=0,games=len(rows),win_rate=0.) for a in ('A','B')};modes={}
    for r in rows:
        modes[r['mode']]=modes.get(r['mode'],0)+1
        for i,a in enumerate(('A','B')):teams[a]['draws' if r['winner'] is None else 'wins' if r['winner']==i else 'losses']+=1
    for value in teams.values():value['win_rate']=value['wins']/max(1,value['games'])
    summary=dict(total_matches=len(rows),teams=teams,modes=modes,policies=[],training=[])
    return dict(schema=1,updated_at=datetime.now(timezone.utc).isoformat(),summary=summary,matches=rows)

def publish(db='data/results.sqlite'):
    import hashlib
    from pathlib import Path
    from cloud.supabase_storage import PrivateStorage
    doc=document(db);store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY'])
    cache_path=Path('data/history-publish-cache.json')
    try:cache=json.loads(cache_path.read_text())
    except (OSError,ValueError):cache={}
    rows=list(reversed(doc['matches']));paths=[]
    for offset in range(0,len(rows),100):
        body=gzip.compress(json.dumps(rows[offset:offset+100],separators=(',',':')).encode(),mtime=0)
        key=f'results-pages/{offset//100:06d}-{hashlib.sha256(body).hexdigest()[:16]}.json.gz';paths.append(key)
        if key not in cache.get('current',[]):store._request('object/'+store.bucket+'/'+key,'PUT',body)
    index=dict(schema=2,total=len(rows),page_size=100,pages=paths,updated_at=doc['updated_at'],summary=doc['summary'])
    store._request('object/'+store.bucket+'/results-index.json','PUT',json.dumps(index).encode())
    from .objective_stats import document as objective_document
    objectives=objective_document(doc['matches']);objectives['updated_at']=doc['updated_at']
    store._request('object/'+store.bucket+'/objective-stats.json.gz','PUT',gzip.compress(json.dumps(objectives,separators=(',',':')).encode(),mtime=0))
    obsolete=set(cache.get('previous',[]))-set(paths)-set(cache.get('current',[]))
    if obsolete:store._request('object/'+store.bucket,'DELETE',json.dumps({'prefixes':sorted(obsolete)}).encode())
    temporary=cache_path.with_suffix('.partial');temporary.write_text(json.dumps(dict(current=paths,previous=cache.get('current',[]))));temporary.replace(cache_path)
    return len(rows)
