from pathlib import Path
import pytest
from server.release_artifacts import capture,fingerprint,verify,sandbox,FOLDERS


def test_frozen_source_and_sandbox_never_copy_secrets_or_production_ledger(tmp_path):
    base=tmp_path/'base';base.mkdir()
    for f in FOLDERS:(base/f).mkdir();(base/f/'a.py').write_text('x=1\n')
    (base/'data').mkdir();(base/'data/results.sqlite').write_text('production-private');(base/'.env').write_text('secret')
    sha=fingerprint(base);runtime=capture(base,tmp_path/'runtime',sha);assert verify(runtime,sha)
    assert not (runtime/'.env').exists()
    isolated=sandbox(runtime,tmp_path/'candidate',base)
    assert not (isolated/'data/results.sqlite').exists()
    assert (isolated/'data/nim-budget').resolve()==base/'data/nim-budget'
    (runtime/'engine/a.py').write_text('changed')
    with pytest.raises(ValueError):verify(runtime,sha)
