import json
import torch
from pathlib import Path
from learning.mission_initialize import initialize
from sb3_contrib import MaskablePPO
import learning.canary_initialize as bootstrap


def test_canary_bootstrap_preserves_both_policies_and_never_trains_or_uses_public_ledger(tmp_path,monkeypatch):
    monkeypatch.chdir(Path.cwd())
    validation=tmp_path/'validation';source=validation/'migrated';source.mkdir(parents=True)
    originals=[]
    for i in (1,2):
        model=initialize(i);model.save(source/f'ppo{i}.zip');bootstrap.export(model,source/f'ppo{i}.npz');originals.append(model)
    (validation/'validation-gates.json').write_text(json.dumps(dict(engine_games=30,release_profile='canary',approved_for_pilot=True)))
    root=tmp_path/'candidate';runtime=tmp_path/'runtime';runtime.mkdir();(tmp_path/'data').mkdir()
    monkeypatch.setattr(bootstrap,'verify',lambda *args:True)
    monkeypatch.setattr(bootstrap,'spool',lambda *args:None)
    monkeypatch.setattr(bootstrap,'publish_pending',lambda *args:{'status':'verified'})
    bootstrap.run(dict(spec=dict(artifact=dict(runtime_digest='pinned')),paths=dict(pilot=str(root),runtime=str(runtime),validation=str(validation))),tmp_path)
    folder=root/json.loads((root/'current.json').read_text())['path']
    for i,original in enumerate(originals,1):
        actual=MaskablePPO.load(folder/f'ppo{i}.zip',device='cpu')
        assert actual.num_timesteps==0
        assert all(torch.equal(value,actual.policy.state_dict()[key]) for key,value in original.policy.state_dict().items())
    state=json.loads((root/'state.json').read_text());assert state['canary'] and state['completed_games']==0 and not state['performance_verified']
    assert not (tmp_path/'data/results.sqlite').exists()
