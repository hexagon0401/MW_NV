import io,json
from cloud.supabase import MetadataStore


def test_metadata_client_defaults_private_and_exposes_only_public_query():
    requests=[]
    def opener(req,**kwargs):requests.append(req);return io.BytesIO(b'[]')
    client=MetadataStore('https://example.supabase.co','fixture-not-a-credential',opener)
    client.insert_private(dict(id='m1',winner=None,scores={},policy_version='rules',replay_uri='private/object',sha256='0'*64))
    assert json.loads(requests[-1].data)['published'] is False
    client.recent_public()
    assert 'published=eq.true' in requests[-1].full_url
    assert 'owner_id' not in requests[-1].full_url
