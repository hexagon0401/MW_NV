import json,io,hashlib
import pytest
from tools.model_download import download


def test_model_pinning_and_corruption_fail_closed(tmp_path):
    body=b'GGUFfixture';manifest=tmp_path/'model.json';target=tmp_path/'hq.gguf'
    data=dict(gguf_url='https://huggingface.co/model/file.gguf',sha256=hashlib.sha256(body).hexdigest(),license_verified=True)
    manifest.write_text(json.dumps(data));download(manifest,target,lambda *a,**kw:io.BytesIO(body))
    assert target.read_bytes()==body
    with pytest.raises(ValueError,match='mismatch'):download(manifest,target,lambda *a,**kw:io.BytesIO(b'bad'))
    assert target.read_bytes()==body and not target.with_suffix('.partial').exists()
    data['license_verified']=False;manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='not verified'):download(manifest,target)
