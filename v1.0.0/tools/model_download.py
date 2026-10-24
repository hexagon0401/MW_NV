"""Download only a reviewed, checksum-pinned GGUF; never execute model contents."""
import hashlib,json,re
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlparse


def download(manifest,destination,opener=urlopen):
    m=json.loads(Path(manifest).read_text());url=m.get('gguf_url');digest=m.get('sha256')
    if not m.get('license_verified') or not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest):raise ValueError('model source/license/checksum not verified')
    if not isinstance(url,str) or urlparse(url).scheme!='https' or urlparse(url).hostname!='huggingface.co':raise ValueError('reviewed HTTPS source required')
    dest=Path(destination)
    if dest.suffix!='.gguf':raise ValueError('GGUF destination required')
    dest.parent.mkdir(parents=True,exist_ok=True);temporary=dest.with_suffix('.partial')
    try:
        h=hashlib.sha256();size=0
        with opener(url,timeout=60) as response,temporary.open('wb') as output:
            if hasattr(response,'geturl') and urlparse(response.geturl()).scheme!='https':raise ValueError('HTTPS redirect required')
            while block:=response.read(1024*1024):
                size+=len(block)
                if size>4*1024**3:raise ValueError('model exceeds size limit')
                output.write(block);h.update(block)
        with temporary.open('rb') as source:magic=source.read(4)
        if h.hexdigest()!=digest or magic!=b'GGUF':raise ValueError('GGUF/checksum mismatch')
        temporary.replace(dest)
    finally:
        temporary.unlink(missing_ok=True)
    return dest


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--manifest',default='config/local-model.json');p.add_argument('--output',default='models/hq.gguf');a=p.parse_args();print(download(a.manifest,a.output))
