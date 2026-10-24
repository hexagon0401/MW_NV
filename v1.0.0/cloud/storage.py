"""S3-compatible final replay upload, read-back checksum, durable retries."""
import gzip,hashlib,json
from pathlib import Path


def upload_replay(client,bucket,source,key,queue):
    source=Path(source);queue=Path(queue)
    body=gzip.compress(source.read_bytes(),mtime=0);digest=hashlib.sha256(body).hexdigest()
    try:
        client.put_object(Bucket=bucket,Key=key,Body=body,ContentType='application/json',ContentEncoding='gzip',Metadata={'sha256':digest})
        received=client.get_object(Bucket=bucket,Key=key)['Body'].read()
        if hashlib.sha256(received).hexdigest()!=digest:raise ValueError('checksum mismatch')
    except Exception as exc:
        items=json.loads(queue.read_text()) if queue.exists() else []
        entry=dict(source=str(source),key=key,bucket=bucket,error=type(exc).__name__)
        items=[i for i in items if (i['key'],i['bucket'])!=(key,bucket)]+[entry]
        queue.parent.mkdir(parents=True,exist_ok=True);temporary=queue.with_suffix('.tmp')
        temporary.write_text(json.dumps(items));temporary.replace(queue)
        return dict(uploaded=False,sha256=digest)
    if queue.exists():
        items=[i for i in json.loads(queue.read_text()) if (i['key'],i['bucket'])!=(key,bucket)]
        queue.write_text(json.dumps(items))
    return dict(uploaded=True,sha256=digest)
