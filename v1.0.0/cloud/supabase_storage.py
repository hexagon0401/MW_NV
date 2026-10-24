"""Private Supabase Storage alternative; server credentials never reach viewer."""
import hashlib,json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote,urlparse


class PrivateStorage:
    def __init__(self,url,key,bucket='mw-nv-replays',opener=urlopen):
        if urlparse(url).scheme!='https':raise ValueError('HTTPS required')
        self.url=url.rstrip('/');self.key=key;self.bucket=bucket;self.opener=opener
    def _request(self,path,method='GET',data=None,content_type='application/json'):
        req=Request(self.url+'/storage/v1/'+path,method=method,data=data,headers={'Authorization':'Bearer '+self.key,'apikey':self.key,'Content-Type':content_type})
        with self.opener(req,timeout=60) as response:return response.read()
    def create_private_bucket(self):
        return self._request('bucket','POST',json.dumps({'id':self.bucket,'name':self.bucket,'public':False}).encode())
    def upload_verified(self,source,key):
        body=Path(source).read_bytes();digest=hashlib.sha256(body).hexdigest()
        path=quote(self.bucket,safe='')+'/'+quote(key,safe='/')
        self._request('object/'+path,'POST',body)
        received=self._request('object/authenticated/'+path)
        if hashlib.sha256(received).hexdigest()!=digest:raise ValueError('storage checksum mismatch')
        return dict(bucket=self.bucket,key=key,sha256=digest,private=True)
