import hashlib,json,shutil
from pathlib import Path
import pytest
from learning import league_archive as archive

def test_chunk_transfer_reconstructs_exact_bytes_and_detects_corruption(tmp_path,monkeypatch):
    remote=tmp_path/'remote';remote.mkdir();source=tmp_path/'bundle.tar.gz';source.write_bytes(b'abc123'*200000);digest=hashlib.sha256(source.read_bytes()).hexdigest()
    def fake(*args,**kwargs):
        if args[:2]==('release','upload'):shutil.copyfile(args[3],remote/Path(args[3]).name)
        elif args[:2]==('release','download'):
            name=args[args.index('--pattern')+1];dest=Path(args[args.index('--dir')+1]);shutil.copyfile(remote/name,dest/name)
        else:raise AssertionError(args)
    monkeypatch.setattr(archive,'gh',fake);transport=archive.transfer(source,'fixture',digest,[])
    assert len(transport['chunks'])==3 and all(c['size']<=524288 for c in transport['chunks'])
    restored=archive.download('fixture',transport,tmp_path/'restored');assert restored.read_bytes()==source.read_bytes()
    (remote/transport['chunks'][0]['name']).write_bytes(b'broken')
    with pytest.raises(ValueError,match='chunk'):archive.download('fixture',transport,tmp_path/'bad')

def test_upload_failure_preserves_pending_and_remote_history(tmp_path,monkeypatch):
    pending=tmp_path/'archive-pending';pending.mkdir();data=pending/'bundle.tar.gz';data.write_bytes(b'payload');meta=dict(asset=data.name,sha256=hashlib.sha256(data.read_bytes()).hexdigest(),full=False)
    (pending/'bundle.tar.json').write_text(json.dumps(meta))
    def fail(*a,**kw):raise RuntimeError('upload failed')
    monkeypatch.setattr(archive,'gh',fail);result=archive.publish_pending(tmp_path)
    assert result['status']=='deferred' and data.exists() and (pending/'bundle.tar.json').exists()
