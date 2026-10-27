"""Small completed-match summaries; immutable generation buckets, no replay downloads."""
import gzip,hashlib,json
from collections import defaultdict
from .results import records


def entries(db):
    out=[]
    for r in records(db,kind='match'):
        if not r.get('ended'):continue
        league=r.get('league',{});generation=league.get('generation')
        for team,learner in league.get('assignments',{}).items():
            if learner not in ('PPO1','PPO2'):continue
            outcome='draw' if r['winner'] is None else 'win' if r['winner']==('A','B').index(team) else 'loss'
            out.append(dict(match=r['id'],run=league.get('run'),learner=learner,generation=generation,execution_kind=r.get('mode'),game_mode=r.get('game_mode'),scenario_id=r.get('scenario_id'),evidence='insufficient',outcome=outcome))
    return out


def compact(rows):
    groups={}
    for r in rows:
        key=tuple(r.get(k) for k in ('run','learner','generation','execution_kind','game_mode','scenario_id','evidence'))
        item=groups.setdefault(key,{**{k:r.get(k) for k in ('run','learner','generation','execution_kind','game_mode','scenario_id','evidence')},'games':0,'wins':0,'losses':0,'draws':0})
        item['games']+=1;item[{'win':'wins','loss':'losses','draw':'draws'}[r['outcome']]]+=1
    return list(groups.values())


def summarize(groups,**filters):
    selected=[r for r in groups if all(v is None or r.get(k)==v for k,v in filters.items())]
    values={k:sum(r[k] for r in selected) for k in ('games','wins','losses','draws')}
    return dict(scope='all_recorded_completed_learner_appearances',complete=True,**values,win_rate=values['wins']/values['games'] if values['games'] else 0,groups=selected)


def document(db,**filters):return summarize(compact(entries(db)),**filters)


def publish(store,db,cache):
    rows=compact(entries(db));buckets=defaultdict(list)
    for r in rows:buckets['unknown' if r['generation'] is None else str(r['generation']//64)].append(r)
    paths=set();refs={};known=cache.setdefault('strategy_hashes',{})
    for bucket,group in sorted(buckets.items()):
        payload=json.dumps(group,sort_keys=True,separators=(',',':')).encode();digest=hashlib.sha256(payload).hexdigest();path='strategy-insights/'+digest+'.json.gz'
        if known.get(bucket)!=digest:store._request('object/'+store.bucket+'/'+path,'PUT',gzip.compress(payload,mtime=0))
        known[bucket]=digest;refs[bucket]=path;paths.add(path)
    # The index is published last; failures preserve the previous complete reference.
    all_generations=[]
    for r in rows:all_generations.append(dict(r,generation=None))
    index=dict(schema=1,buckets=refs,lifetime=compact_totals(all_generations))
    path='strategy-insights/index.json.gz';store._request('object/'+store.bucket+'/'+path,'PUT',gzip.compress(json.dumps(index,separators=(',',':')).encode(),mtime=0));paths.add(path)
    return paths


def compact_totals(rows):
    out={}
    for r in rows:
        key=tuple(r.get(k) for k in ('run','learner','execution_kind','game_mode','scenario_id','evidence'))
        item=out.setdefault(key,{k:v for k,v in r.items() if k not in ('generation','games','wins','losses','draws')})
        for k in ('games','wins','losses','draws'):item[k]=item.get(k,0)+r[k]
    return list(out.values())
