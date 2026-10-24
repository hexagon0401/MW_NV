"""Publish completed local views into private Storage without requiring SQL setup."""
import argparse,json,os,re,gzip,tempfile
from pathlib import Path
from urllib.error import HTTPError
from .supabase_storage import PrivateStorage


def publish(source,match_id):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',match_id):raise ValueError('invalid match ID')
    doc=json.loads(Path(source).read_text())
    if not doc.get('summary',{}).get('ended'):raise ValueError('only completed matches')
    store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY'])
    try:store.create_private_bucket()
    except HTTPError as e:
        if e.code not in (400,409):raise
    key=match_id+'.view.json'
    if Path(source).stat().st_size>=1024*1024:
        key+='.gz'
        with tempfile.NamedTemporaryFile(suffix='.json.gz') as packed:
            packed.write(gzip.compress(Path(source).read_bytes(),mtime=0));packed.flush()
            verified=store.upload_verified(packed.name,key)
    else:verified=store.upload_verified(source,key)
    try:entries=json.loads(store._request('object/authenticated/'+store.bucket+'/index.json'))
    except HTTPError as e:
        if e.code not in (400,404):raise
        entries=[]
    summary=doc['summary']
    entry=dict(id=match_id,scores=summary['scores'],winner=summary.get('winner'),policy_version=doc.get('rules_version'),replay_uri='supabase://'+store.bucket+'/'+key,sha256=verified['sha256'])
    entries=[entry]+[e for e in entries if e['id']!=match_id]
    # Single operator only: manifest replacement is not a multi-writer transaction.
    store._request('object/'+store.bucket+'/index.json','PUT',json.dumps(entries[:20]).encode())
    return dict(id=match_id,sha256=verified['sha256'],private=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--view',required=True);parser.add_argument('--id',required=True);a=parser.parse_args()
    print(json.dumps(publish(a.view,a.id)))
