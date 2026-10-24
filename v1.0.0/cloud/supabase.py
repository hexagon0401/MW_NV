"""Backend-only metadata client. RLS remains the server's authority."""
import json
from urllib.parse import urlparse
from urllib.request import Request,urlopen


class MetadataStore:
    def __init__(self,url,key,opener=urlopen):
        parsed=urlparse(url)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:raise ValueError('HTTPS project URL required')
        self.url=url.rstrip('/');self.key=key;self.opener=opener
    def _request(self,path,data=None):
        headers={'apikey':self.key,'Authorization':'Bearer '+self.key,'Content-Type':'application/json'}
        req=Request(self.url+'/rest/v1/'+path,headers=headers,data=None if data is None else json.dumps(data).encode())
        with self.opener(req,timeout=20) as response:
            raw=response.read(1024*1024)
        return json.loads(raw) if raw else None
    def recent_public(self):
        return self._request('mw_nv_matches?published=eq.true&select=id,started_at,winner,scores,policy_version,replay_uri,sha256&order=started_at.desc&limit=20')
    def insert_private(self,metadata):
        fields={'id','winner','scores','policy_version','replay_uri','sha256'}
        if set(metadata)!=fields:raise ValueError('match metadata fields')
        return self._request('mw_nv_matches',metadata|{'published':False})
