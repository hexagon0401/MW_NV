"""Compatible JSON/gzip checkpoint writer: C encoder, compact JSON, fast compression."""
import gzip,json
from engine.replay import encode

def write_environment(path,value):
    # One bounded snapshot per file; never remove events or change RNG/world state.
    payload=json.dumps(encode(value),separators=(',',':'),allow_nan=False).encode('utf-8')
    with gzip.open(path,'wb',compresslevel=1) as output:output.write(payload)

def commit_metadata(root,state):
    """No world/model/RNG changes since last save: persist only archive counters."""
    from pathlib import Path
    from .self_play import atomic_json
    root=Path(root);folder=root/json.loads((root/'current.json').read_text())['path']
    previous=json.loads((folder/'state.json').read_text())
    if previous['generation']!=state['generation']:raise ValueError('checkpoint generation mismatch')
    atomic_json(folder/'state.json',state);atomic_json(root/'state.json',state)
