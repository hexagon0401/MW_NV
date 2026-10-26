"""Immutable policy/recovery spool. Never delete unverified local or old remote assets."""
import gzip,hashlib,json,tarfile,tempfile,time,shutil,os
from datetime import datetime,timezone
from pathlib import Path
from .backup import gh,restore,REPO
from .self_play import atomic_json


def spool(root,checkpoint,state,full=False):
    root=Path(root);folder=root/'archive-pending';folder.mkdir(exist_ok=True)
    name=f'{state["run"]}-{state["completed_games"]:08d}-{state["generation"]:08d}-'+('recovery' if full else 'policies')+'.tar.gz';path=folder/name
    if path.exists():return path
    temporary=path.with_suffix('.partial')
    with tarfile.open(temporary,'w:gz') as tar:
        for p in sorted(Path(checkpoint).iterdir()):
            if p.is_file() and (full or p.name in ('ppo1.npz','ppo2.npz','PPO1.json','PPO2.json','state.json')):tar.add(p,arcname=p.name)
        if full:
            for p in sorted((root/'opponents').glob('*.npz')):tar.add(p,arcname='opponents/'+p.name)
            for p in sorted((root/'baseline').glob('*.npz')):tar.add(p,arcname='baseline/'+p.name)
        from .results import records
        body=''.join(json.dumps(r,separators=(',',':'))+'\n' for r in records('data/results.sqlite') if r.get('league',{}).get('run')==state['run']).encode()
        import io
        info=tarfile.TarInfo('statistics.jsonl');info.size=len(body);tar.addfile(info,io.BytesIO(body))
    temporary.replace(path)
    atomic_json(path.with_suffix('.json'),dict(asset=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),full=full,run=state['run'],games=state['completed_games'],generation=state['generation']))
    return path


def verify(path,digest,full):
    from .candidate_policy import CandidatePolicy
    from sb3_contrib import MaskablePPO
    from engine.replay import decode
    from engine.runtime import Engine
    from engine.version import RULES_VERSION
    import numpy as np
    with tempfile.TemporaryDirectory() as tmp:
        # Dedicated archive limits account for two models, ledger and opponent pool.
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('archive checksum')
        with tarfile.open(path,'r:gz') as tar:
            entries=tar.getmembers()
            if len(entries)>100 or sum(e.size for e in entries)>512*1024**2:raise ValueError('archive size')
            if any(not e.isfile() or Path(e.name).is_absolute() or '..' in Path(e.name).parts or len(Path(e.name).parts)>2 for e in entries):raise ValueError('archive path')
            tar.extractall(tmp,filter='data')
        p=Path(tmp);state=json.loads((p/'state.json').read_text())
        if state['rules_version']!=RULES_VERSION or state['contract']!='tactics-2':raise ValueError('archive contract')
        for i in (1,2):
            policy=CandidatePolicy(p/f'ppo{i}.npz')
            if full:
                model=MaskablePPO.load(p/f'ppo{i}.zip',device='cpu');obs=np.zeros(1056,dtype=np.float32);mask=np.ones(65,dtype=bool)
                if int(model.predict(obs,deterministic=True,action_masks=mask)[0])!=policy.predict(obs,mask):raise ValueError('archive inference mismatch')
        if full:
            with gzip.open(p/'environment.json.gz','rt') as f:doc=json.load(f)
            a=Engine(decode(doc)['world']);b=Engine(decode(doc)['world']);a.step(.2);b.step(.2)
            if a.world.checksum()!=b.world.checksum():raise ValueError('archive isolated replay mismatch')
        return True


def publish_pending(root):
    root=Path(root)
    if shutil.disk_usage(root).free<1024**3 or sum(p.stat().st_size for p in (root/'archive-pending').glob('*'))>=2*1024**3:raise RuntimeError('ARCHIVE_DISK_LIMIT')
    failures=[]
    for manifest in sorted((root/'archive-pending').glob('*.json')):
        metadata=json.loads(manifest.read_text());path=manifest.with_suffix('.tar.gz')
        # with_suffix on foo.tar.json produces foo.tar.tar.gz; canonical name is in manifest.
        path=manifest.parent/metadata['asset']
        try:
            month=datetime.now(timezone.utc).strftime('%Y-%m');part=1
            while True:
                tag=f'training-{month}-{part:03d}'
                try:release=json.loads(gh('api',f'repos/{REPO}/releases/tags/{tag}'))
                except RuntimeError:
                    gh('release','create',tag,'--repo',REPO,'--target','dev/v1.0.0','--title',tag,'--notes','Immutable verified policy/recovery history.','--latest=false');release=json.loads(gh('api',f'repos/{REPO}/releases/tags/{tag}'))
                needed=(path.stat().st_size+524287)//524288+1
                if len(release.get('assets',[]))+needed<=250 or any(a['name'].startswith(path.name+'.part') for a in release.get('assets',[])):break
                part+=1
            transport=transfer(path,tag,metadata['sha256'],release.get('assets',[]))
            with tempfile.TemporaryDirectory() as tmp:
                received=download(tag,transport,Path(tmp));verify(received,metadata['sha256'],metadata['full'])
            metadata['transport']=transport
            metadata.update(release=tag,status='verified')
            import base64
            branch='training/checkpoints';remote=f'repos/{REPO}/contents/archive/{path.name}.json'
            payload=dict(message=f'Archive {path.name}',branch=branch,content=base64.b64encode(json.dumps(metadata).encode()).decode())
            try:payload['sha']=json.loads(gh('api',remote+'?ref=training/checkpoints'))['sha']
            except RuntimeError:pass
            # The metadata branch already exists in this repository; create it if absent.
            try:gh('api',f'repos/{REPO}/git/ref/heads/training/checkpoints')
            except RuntimeError:
                sha=json.loads(gh('api',f'repos/{REPO}/git/ref/heads/dev/v1.0.0'))['object']['sha'];gh('api',f'repos/{REPO}/git/refs','--method','POST','--input','-',data={'ref':'refs/heads/training/checkpoints','sha':sha})
            gh('api',remote,'--method','PUT','--input','-',data=payload)
            dest=root/'archive-verified';dest.mkdir(exist_ok=True);atomic_json(dest/manifest.name,metadata)
            path.unlink();manifest.unlink()
        except Exception as exc:
            failures.append(dict(asset=path.name,error=type(exc).__name__,detail=str(exc)[:300]));break
    result=dict(status='deferred' if failures else 'verified',failures=failures,pending=len(list((root/'archive-pending').glob('*.json'))));atomic_json(root/'archive-status.json',result);return result


def transfer(path,tag,digest,assets):
    """512KiB objects avoid this environment's failing large-body upload path."""
    path=Path(path);existing={a['name'] for a in assets};chunks=[]
    with tempfile.TemporaryDirectory() as tmp:
        with path.open('rb') as source:
            index=0
            while body:=source.read(524288):
                name=path.name+f'.part{index:03d}';part=Path(tmp)/name;part.write_bytes(body)
                chunks.append(dict(name=name,sha256=hashlib.sha256(body).hexdigest(),size=len(body)))
                if name not in existing:gh('release','upload',tag,str(part),'--repo',REPO)
                index+=1
        transport=dict(asset=path.name,sha256=digest,chunks=chunks)
        manifest=Path(tmp)/(path.name+'.manifest.json');manifest.write_text(json.dumps(transport,sort_keys=True))
        if manifest.name not in existing:gh('release','upload',tag,str(manifest),'--repo',REPO)
    return transport


def download(tag,transport,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);target=directory/transport['asset']
    with target.open('wb') as output:
        for chunk in transport['chunks']:
            gh('release','download',tag,'--repo',REPO,'--pattern',chunk['name'],'--dir',str(directory))
            path=directory/chunk['name'];body=path.read_bytes()
            if len(body)!=chunk['size'] or hashlib.sha256(body).hexdigest()!=chunk['sha256']:raise ValueError('remote chunk checksum')
            output.write(body);path.unlink()
    if hashlib.sha256(target.read_bytes()).hexdigest()!=transport['sha256']:raise ValueError('remote archive checksum')
    return target


def restore_bundle(path,destination,digest):
    """Restore to a new root only; the caller keeps both source and remote history."""
    verify(path,digest,True);root=Path(destination)
    if root.exists() and any(root.iterdir()):raise ValueError('restore destination must be empty')
    root.mkdir(parents=True,exist_ok=True);checkpoint=root/'checkpoints'/'restored';checkpoint.mkdir(parents=True)
    with tarfile.open(path,'r:gz') as tar:tar.extractall(checkpoint,filter='data')
    for name in ('baseline','opponents'):
        source=checkpoint/name
        if source.exists():shutil.move(source,root/name)
        else:(root/name).mkdir()
    if (checkpoint/'results.sqlite').exists():shutil.copyfile(checkpoint/'results.sqlite',root/'results.sqlite')
    atomic_json(root/'current.json',dict(path='checkpoints/restored'));shutil.copyfile(checkpoint/'state.json',root/'state.json')
    return root


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('restore');a.add_argument('--archive',required=True);a.add_argument('--sha256',required=True);a.add_argument('--root',required=True)
    a=sub.add_parser('download');a.add_argument('--manifest',required=True);a.add_argument('--tag',required=True);a.add_argument('--output',required=True)
    args=p.parse_args()
    if args.command=='restore':print(restore_bundle(args.archive,args.root,args.sha256))
    else:print(download(args.tag,json.loads(Path(args.manifest).read_text()),Path(args.output)))
