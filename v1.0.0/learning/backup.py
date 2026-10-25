"""Verified replaceable Release backup, separate metadata branch, no binary Git history."""
import hashlib,json,subprocess,tarfile,tempfile,shutil
from pathlib import Path
REPO='hexagon0401/MW_NV'

def gh(*args,data=None,binary=False):
    result=subprocess.run(['gh',*args],input=None if data is None else json.dumps(data).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace')[:500])
    return result.stdout if binary else result.stdout.decode()

def pack(root,generation):
    root=Path(root);directory=root/'backups';directory.mkdir(exist_ok=True)
    archive=directory/f'checkpoint-{generation:08d}.tar.gz'
    if archive.exists():return archive,hashlib.sha256(archive.read_bytes()).hexdigest()
    saved=root/json.loads((root/'current.json').read_text())['path'] if (root/'current.json').exists() else root
    files=['latest.zip','latest.npz','teacher.npz','environment.json','monitor.json','results.sqlite','rng.json','state.json','A.json','B.json','champion.npz','opponents.json']
    with tarfile.open(archive,'w:gz') as tar:
        for name in files:
            path=(saved/name) if (saved/name).is_file() else root/name
            if path.is_file():tar.add(path,arcname=name)
        for path in sorted((root/'opponents').glob('*.npz')):tar.add(path,arcname='opponents/'+path.name)
    verified=None
    if (root/'backup-status.json').exists():
        try:verified=json.loads((root/'backup-status.json').read_text()).get('asset')
        except (ValueError,TypeError):pass
    paths=sorted(directory.glob('checkpoint-*.tar.gz'));keep={archive.name,verified} if verified else {p.name for p in paths[-2:]}
    for old in paths:
        if old.name not in keep:old.unlink()
    return archive,hashlib.sha256(archive.read_bytes()).hexdigest()

def restore(archive,root,sha256):
    archive=Path(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=sha256:raise ValueError('backup checksum mismatch')
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    with tarfile.open(archive,'r:gz') as tar:
        entries=tar.getmembers()
        if len(entries)>40 or sum(e.size for e in entries)>256*1024*1024:raise ValueError('backup size')
        for e in entries:
            p=Path(e.name)
            if not e.isfile() or p.is_absolute() or '..' in p.parts or len(p.parts)>2:raise ValueError('unsafe backup path')
        tar.extractall(root,filter='data')

def publish(root,generation):
    root=Path(root);archive,digest=pack(root,generation)
    try:release=json.loads(gh('api',f'repos/{REPO}/releases/tags/training-latest'))
    except RuntimeError:
        gh('release','create','training-latest','--repo',REPO,'--target','dev/v1.0.0','--title','Latest training recovery','--notes','Verified machine-readable training recovery.','--latest=false')
        release=json.loads(gh('api',f'repos/{REPO}/releases/tags/training-latest'))
    # Generation names are immutable; an interrupted retry must not delete a verified old generation.
    assets=release.get('assets',[]);existing=next((a for a in assets if a['name']==archive.name),None)
    if existing:
        with tempfile.TemporaryDirectory() as tmp:
            gh('release','download','training-latest','--repo',REPO,'--pattern',archive.name,'--dir',tmp)
            if hashlib.sha256((Path(tmp)/archive.name).read_bytes()).hexdigest()!=digest:raise ValueError('generation already exists with different contents')
    else:gh('release','upload','training-latest',str(archive),'--repo',REPO)
    with tempfile.TemporaryDirectory() as tmp:
        gh('release','download','training-latest','--repo',REPO,'--pattern',archive.name,'--dir',tmp)
        if hashlib.sha256((Path(tmp)/archive.name).read_bytes()).hexdigest()!=digest:raise ValueError('remote checksum mismatch')
    manifest=dict(generation=generation,asset=archive.name,sha256=digest,completed_games=json.loads((root/'state.json').read_text())['completed_games'])
    gh('release','edit','training-latest','--repo',REPO,'--notes',json.dumps(manifest))
    # Metadata commits do not touch the active working tree or code branch.
    try:gh('api',f'repos/{REPO}/git/ref/heads/training/checkpoints')
    except RuntimeError:
        sha=json.loads(gh('api',f'repos/{REPO}/git/ref/heads/dev/v1.0.0'))['object']['sha']
        gh('api',f'repos/{REPO}/git/refs','--method','POST','--input','-',data={'ref':'refs/heads/training/checkpoints','sha':sha})
    import base64
    payload=dict(message=f'Training checkpoint {generation}',branch='training/checkpoints',content=base64.b64encode(json.dumps(manifest,indent=2).encode()).decode())
    try:payload['sha']=json.loads(gh('api',f'repos/{REPO}/contents/training-checkpoint.json?ref=training/checkpoints'))['sha']
    except RuntimeError:pass
    gh('api',f'repos/{REPO}/contents/training-checkpoint.json','--method','PUT','--input','-',data=payload)
    for asset in assets:
        if asset['name'].startswith('checkpoint-') and asset['name']!=archive.name:gh('api',f'repos/{REPO}/releases/assets/{asset["id"]}','--method','DELETE')
    (root/'backup-status.json').write_text(json.dumps(dict(manifest,status='verified')))
    # Keep last verified generation and the newest pending generation locally.
    for old in sorted((root/'backups').glob('checkpoint-*.tar.gz'))[:-2]:
        if old!=archive:old.unlink()
    return manifest
