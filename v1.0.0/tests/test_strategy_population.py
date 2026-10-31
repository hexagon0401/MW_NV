import random
import numpy as np
import pytest
from learning.opponent_population import Population,select,record_payoff
from learning.online_metrics import merge


def test_population_cap_and_heldout_exclusion(tmp_path):
    p=Population(tmp_path);folder=tmp_path/'opponents';folder.mkdir()
    for i in range(40):
        f=folder/f'{i}.npz';f.write_bytes(str(i).encode());p.register(f,i,remote={'fixture':True})
    assert len(p.state['entries'])==32
    assert min(e['generation'] for e in p.state['entries'])==0
    counts={}
    for i in range(24):
        e=select(p.state['entries'],{},i,counts);counts[e['id']]=counts.get(e['id'],0)+1
    assert max(counts.values())<=6
    with pytest.raises(ValueError):record_payoff(p.state,'x',1,partition='heldout')


def test_cache_rejects_corruption_and_preserves_unverified(tmp_path):
    p=Population(tmp_path);folder=tmp_path/'opponents';folder.mkdir()
    for i in range(10):
        f=folder/f'{i}.npz';f.write_bytes(str(i).encode());p.register(f,i)
    assert p.prune()['blocked_unverified']==2
    e=p.state['entries'][0];(folder/e['file']).unlink()
    e['remote']={'fixture':True}
    with pytest.raises(ValueError):p.resolve(e,lambda _,f:f.write_bytes(b'wrong'))
    assert not (folder/e['file']).exists()


def test_running_moments_match_full_data():
    a=merge(None,[1,2,3]);a=merge(a,[4,5])
    assert a['count']==5 and np.isclose(a['mean'],3) and np.isclose(a['variance'],2)
