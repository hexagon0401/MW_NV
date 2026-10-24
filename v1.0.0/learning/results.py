"""Local completed-match ledger and idempotent portable JSONL records."""
import argparse,json,sqlite3,uuid,hashlib
from pathlib import Path
from datetime import datetime,timezone

SCHEMA='''CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL);'''


def validate(record):
    if not isinstance(record,dict) or record.get('kind') not in ('match','training'):raise ValueError('record kind')
    if not isinstance(record.get('id'),str) or not 1<=len(record['id'])<=128:raise ValueError('record id')
    if not isinstance(record.get('rules_version'),str) or not isinstance(record.get('policies'),dict) or set(record['policies'])!={'A','B'} or any(not isinstance(v,str) or not v for v in record['policies'].values()):raise ValueError('rules/policy versions')
    if record['kind']=='match':
        if record.get('mode') not in ('training','evaluation','hybrid','rules'):raise ValueError('mode')
        if record.get('winner') is not None and type(record['winner']) is not int:raise ValueError('winner')
        if record.get('winner') not in (None,0,1) or record.get('ended') is not True:raise ValueError('completed match required')
        if type(record.get('seed')) is not int or not isinstance(record.get('scores'),list) or len(record['scores'])!=2 or any(type(s) is not int or s<0 for s in record['scores']):raise ValueError('seed/scores')
    elif record.get('training_run') is not None and (not isinstance(record['training_run'],str) or not record['training_run']):raise ValueError('training run')
    elif type(record.get('steps')) is not int or record['steps']<0:raise ValueError('training steps')
    return record


def insert(db,record):
    validate(record);db=Path(db);db.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False)
    with sqlite3.connect(db,timeout=10) as conn:
        conn.execute(SCHEMA);existing=conn.execute('SELECT payload FROM records WHERE id=?',(record['id'],)).fetchone()
        if existing:
            if existing[0]!=payload:raise ValueError('record id conflict')
            return False
        conn.execute('INSERT INTO records VALUES (?,?,?)',(record['id'],record['kind'],payload))
    return True


def record_world(db,w,mode,policies,match_id=None,steps=0):
    if not getattr(w,'ended',False):return False
    return insert(db,dict(kind='match',id=match_id or uuid.uuid4().hex,rules_version=w.rules_version,catalog_version=w.catalog_version,mode=mode,policies=policies,seed=w.seed,swapped=getattr(w,'swapped',False),winner=None if w.winner is None else int(w.winner),scores=[w.teams[t].score for t in (0,1)],ended=True,ticks=w.tick,created_at=datetime.now(timezone.utc).isoformat()))


def record_training(db,policy,steps,opponent='algorithm',run_id=None,training_run=None):
    return insert(db,dict(kind='training',id=run_id or uuid.uuid4().hex,rules_version='combined-arms-1',policies={'A':policy,'B':opponent},steps=int(steps),training_run=training_run))


def records(db):
    path=Path(db)
    if not path.exists():return []
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as conn:
        return [json.loads(row[0]) for row in conn.execute('SELECT payload FROM records ORDER BY id')]


def aggregate(db):
    values=records(db);teams={a:dict(wins=0,losses=0,draws=0,games=0,win_rate=0.) for a in ('A','B')};groups={};steps={};training_totals={};total=0
    for r in values:
        if r['kind']=='training':
            key=(r['rules_version'],r['policies']['A']);steps[key]=steps.get(key,0)+r['steps'];training_totals[key]=training_totals.get(key,0)+r['steps']
            if r.get('training_run'):
                alias=(r['rules_version'],r['training_run']);steps[alias]=steps.get(alias,0)+r['steps']
            continue
        total+=1
        for i,a in enumerate(('A','B')):
            outcome='draws' if r['winner'] is None else 'wins' if r['winner']==i else 'losses'
            teams[a][outcome]+=1;teams[a]['games']+=1
            key=(r['rules_version'],r['mode'],r['policies'][a],r['policies']['B' if a=='A' else 'A'])
            group=groups.setdefault(key,dict(rules_version=key[0],mode=key[1],policy=key[2],opponent=key[3],wins=0,losses=0,draws=0,games=0))
            group[outcome]+=1;group['games']+=1
    for t in teams.values():t['win_rate']=t['wins']/t['games'] if t['games'] else 0.
    for g in groups.values():g['win_rate']=g['wins']/g['games'];g['training_steps']=steps.get((g['rules_version'],g['policy']),0)
    return dict(total_matches=total,teams=teams,policies=list(groups.values()),training=[dict(rules_version=k[0],policy=k[1],steps=v) for k,v in sorted(training_totals.items())])


def export_records(db,output):
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records(db)))


def import_records(db,source):
    # Validate the whole bundle before writing, then use one transaction.
    batch=[validate(json.loads(line)) for line in Path(source).read_text().splitlines() if line.strip()]
    path=Path(db);path.parent.mkdir(parents=True,exist_ok=True);added=0
    with sqlite3.connect(path) as conn:
        conn.execute(SCHEMA)
        for record in batch:
            payload=json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False)
            existing=conn.execute('SELECT payload FROM records WHERE id=?',(record['id'],)).fetchone()
            if existing and existing[0]!=payload:raise ValueError('record id conflict')
            if not existing:conn.execute('INSERT INTO records VALUES (?,?,?)',(record['id'],record['kind'],payload));added+=1
    return added


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['show','export','import']);p.add_argument('--db',default='data/results.sqlite');p.add_argument('--file',default='data/results.jsonl');a=p.parse_args()
    if a.action=='export':export_records(a.db,a.file)
    elif a.action=='import':print(import_records(a.db,a.file))
    else:print(json.dumps(aggregate(a.db),ensure_ascii=False,indent=2))
