import json
import pytest
from server.releases import Registry
from test_releases import spec,cmd


def test_comparison_never_automatically_starts(tmp_path):
    registry=Registry(tmp_path);s=spec();s['handler']='policy_comparison';d=registry.register(s)
    registry.observe('test',dict(steps=[dict(id='engine',state='PASS')],evidence_digest=d))
    with pytest.raises(ValueError,match='manual'):registry.command(cmd(d,'set_auto',True))
    assert registry.pending() is None


def test_comparison_run_preserves_weights_and_releases_cpu_reservation(tmp_path,monkeypatch):
    import learning.league_evaluate as evaluator
    from sb3_contrib import MaskablePPO
    from server.policy_comparison import run
    root=tmp_path/'comparison';root.mkdir();(tmp_path/'data/releases').mkdir(parents=True)
    (root/'manifest.json').write_text(json.dumps(dict(base=str(tmp_path),old_games=200,new_games=765,generation=100,release_id='test')))
    for i in (1,2):(root/f'ppo{i}.zip').write_bytes(b'fixed-weight')
    monkeypatch.setattr(MaskablePPO,'load',lambda *a,**kw:object())
    def evaluate(path,models,state,progress):
        progress();assert len(models)==2
        return dict(results=[dict(learner=learner,opponent='initial',seed=seed,score=1.) for learner in ('PPO1','PPO2') for seed in range(5)])
    monkeypatch.setattr(evaluator,'evaluate',evaluate);original=evaluator.record_world
    run(root)
    assert evaluator.record_world is original
    result=json.loads((root/'job.json').read_text());assert result['state']=='COMPLETED' and result['summary']['PPO1']['wins']==5
    assert not (tmp_path/'data/releases/reservation.json').exists()
    assert (root/'ppo1.zip').read_bytes()==b'fixed-weight'
