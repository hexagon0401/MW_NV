"""Bounded latest completed training replay, uploaded at simulation speed."""
import gzip,json,hashlib,os
from engine.viewer_export import export_view
from cloud.supabase_storage import PrivateStorage

def publish_latest(engine,initial):
    doc=export_view(engine,initial);body=gzip.compress(json.dumps(doc,separators=(',',':')).encode(),mtime=0)
    store=PrivateStorage(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY']);key='training-latest.view.json.gz'
    store._request('object/'+store.bucket+'/'+key,'PUT',body)
    received=store._request('object/authenticated/'+store.bucket+'/'+key)
    digest=hashlib.sha256(body).hexdigest()
    if hashlib.sha256(received).hexdigest()!=digest:raise ValueError('replay checksum')
    entries=json.loads(store._request('object/authenticated/'+store.bucket+'/index.json'))
    entry=dict(id='training-latest',scores=doc['summary']['scores'],winner=doc['summary']['winner'],policy_version=doc['rules_version'],replay_uri='supabase://'+store.bucket+'/'+key,sha256=digest,mode='training')
    entries=[entry]+[e for e in entries if e['id']!='training-latest']
    store._request('object/'+store.bucket+'/index.json','PUT',json.dumps(entries[:20]).encode())
