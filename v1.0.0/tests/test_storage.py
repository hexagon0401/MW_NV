import io,json
from cloud.storage import upload_replay


def test_upload_checksum_failure_and_retry_keep_source(tmp_path):
    class Client:
        fail=True
        def put_object(self,**args):
            if self.fail:raise OSError('offline')
            self.body=args['Body']
        def get_object(self,**args):return {'Body':io.BytesIO(self.body)}
    c=Client();source=tmp_path/'match.json';source.write_text('{"done":true}')
    queue=tmp_path/'queue.json'
    assert not upload_replay(c,'private',source,'match.gz',queue)['uploaded']
    assert source.exists() and len(json.loads(queue.read_text()))==1
    c.fail=False
    assert upload_replay(c,'private',source,'match.gz',queue)['uploaded']
    assert json.loads(queue.read_text())==[]
