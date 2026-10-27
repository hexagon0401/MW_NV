"""Developer-side registration of fixed Pages artifacts; never exposed as a shell API."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from .releases import Registry,ID
from .release_handlers import digest_files
from .telemetry import atomic
from .release_observations import read


def pages(registry,source,id,revision,title,description):
    if not ID.fullmatch(id) or revision<1:raise ValueError('invalid release identity')
    destination=registry.root.resolve()/'artifacts'/id/str(revision)
    if destination.exists():raise ValueError('artifact revision already exists')
    destination.mkdir(parents=True);viewer=destination/'viewer';viewer.mkdir();source=Path(source).resolve()
    for folder in ('dist','src','functions'):
        shutil.copytree(source/folder,viewer/folder,ignore=shutil.ignore_patterns('.env*','*.key','node_modules','__pycache__'))
    for file in ('wrangler.jsonc','package.json','package-lock.json'):
        if (source/file).exists():shutil.copy2(source/file,viewer/file)
    git=subprocess.run(['git','rev-parse','HEAD'],cwd=source,capture_output=True,text=True,check=True).stdout.strip()
    atomic(viewer/'dist/release-marker.json',dict(release_id=id,revision=revision,source_commit=git))
    manifest={str(p.relative_to(destination)):hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.rglob('*') if p.is_file()}
    atomic(destination/'files.json',manifest);sha=digest_files(manifest)
    atomic(destination/'validation.json',dict(artifact_sha256=sha,tests=False,build=False,preview=False,rollback=False))
    spec=dict(id=id,revision=revision,title=title,description=description,targets=['site'],dependencies=[],handler='pages_site',artifact=dict(artifact_id=id+'-'+str(revision),sha256=sha,source_commit=git),validation_plan=['tests','build','preview','rollback'],planned=False)
    definitions=registry.root/'definitions';definitions.mkdir(exist_ok=True);atomic(definitions/(id+'.json'),dict(spec=spec,paths=dict(artifact=str(destination))));registry.register(spec);return sha


def certify(registry,id,report):
    definition=read(registry.root/'definitions'/(id+'.json'));expected=definition['spec']['artifact']['sha256']
    if report.get('artifact_sha256')!=expected or any(type(report.get(k))is not bool for k in ('tests','build','preview','rollback')):raise ValueError('proof does not identify fixed artifact')
    atomic(Path(definition['paths']['artifact'])/'validation.json',report)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['pages','certify']);p.add_argument('--root',default='data/releases');p.add_argument('--id',required=True);p.add_argument('--revision',type=int,default=1);p.add_argument('--source');p.add_argument('--title');p.add_argument('--description',default='');p.add_argument('--report');a=p.parse_args();r=Registry(a.root)
    if a.action=='pages':print(pages(r,a.source,a.id,a.revision,a.title,a.description))
    else:certify(r,a.id,json.loads(Path(a.report).read_text()))
