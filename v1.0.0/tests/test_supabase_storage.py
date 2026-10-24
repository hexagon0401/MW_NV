import io,json
from cloud.supabase_storage import PrivateStorage


def test_private_bucket_and_authenticated_readback(tmp_path):
    requests=[];body=b'{"match":1}';source=tmp_path/'m.json';source.write_bytes(body)
    def opener(req,**kwargs):
        requests.append(req)
        return io.BytesIO(body if '/authenticated/' in req.full_url else b'{}')
    s=PrivateStorage('https://example.supabase.co','fixture-key',opener=opener)
    s.create_private_bucket();assert json.loads(requests[0].data)['public'] is False
    result=s.upload_verified(source,'m.json')
    assert result['private'] and '/authenticated/' in requests[-1].full_url
