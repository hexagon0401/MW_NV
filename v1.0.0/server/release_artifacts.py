"""Immutable source/artifact capture; no environment values, models or logs copied."""
import hashlib,json,shutil
from pathlib import Path
from .telemetry import atomic

FOLDERS=('engine','agents','learning','config','server','cloud')

def fingerprint(root):
    root=Path(root);files=sorted(p for folder in FOLDERS[:5] for p in (root/folder).glob('*') if p.suffix in ('.py','.yaml'))
    return hashlib.sha256(b''.join(str(p.relative_to(root)).encode()+p.read_bytes() for p in files)).hexdigest()


def capture(base,destination,expected):
    base=Path(base).resolve();destination=Path(destination)
    if destination.exists():
        if fingerprint(destination)!=expected:raise ValueError('immutable runtime changed')
        verify(destination,expected);return destination
    if fingerprint(base)!=expected:raise ValueError('source does not match validated build')
    temporary=destination.with_name(destination.name+'.partial');shutil.rmtree(temporary,ignore_errors=True);temporary.mkdir(parents=True)
    for name in FOLDERS:
        shutil.copytree(base/name,temporary/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ('requirements.lock','requirements.txt','pyproject.toml'):
        if (base/name).exists():shutil.copy2(base/name,temporary/name)
    (temporary/'data').symlink_to(base/'data',target_is_directory=True)
    if fingerprint(temporary)!=expected:raise ValueError('runtime copy checksum')
    files={str(p.relative_to(temporary)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in FOLDERS for p in (temporary/folder).rglob('*') if p.is_file()}
    atomic(temporary/'artifact-files.json',files)
    temporary.rename(destination);return destination


def sandbox(runtime,directory,base):
    runtime=Path(runtime).resolve();directory=Path(directory).resolve();directory.mkdir(parents=True,exist_ok=True)
    for name in FOLDERS:
        link=directory/name
        if not link.exists():link.symlink_to(runtime/name,target_is_directory=True)
        if link.resolve()!=runtime/name:raise ValueError('sandbox runtime conflict')
    data=directory/'data';data.mkdir(exist_ok=True);broker=data/'nim-budget';shared=Path(base).resolve()/'data/nim-budget';shared.mkdir(exist_ok=True)
    if not broker.exists():broker.symlink_to(shared,target_is_directory=True)
    if broker.resolve()!=shared:raise ValueError('sandbox NIM budget must be shared')
    return directory


def verify(runtime,expected):
    root=Path(runtime)
    if fingerprint(root)!=expected:raise ValueError('runtime fingerprint changed')
    manifest=json.loads((root/'artifact-files.json').read_text())
    for name,sha in manifest.items():
        p=(root/name).resolve()
        if not p.is_relative_to(root.resolve()) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('runtime file changed')
    return True
