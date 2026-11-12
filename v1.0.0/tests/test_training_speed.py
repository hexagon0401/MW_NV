import json
import pytest
from learning.training_status import Reporter

@pytest.fixture
def clock(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);(tmp_path/'data').mkdir()
    monkeypatch.delenv('MW_NV_PUBLISH_TRAINING',raising=False)
    now=[0.]
    monkeypatch.setattr('learning.training_status.time.monotonic',lambda:now[0])
    return tmp_path,now

def read(root):return json.loads((root/'training-status.json').read_text())

def test_training_uses_recent_window_not_session_average(clock):
    root,now=clock;r=Reporter(root,0)
    now[0]=30;r(dict(phase='learning',sim_seconds=360))
    assert read(root)['sim_speed']==12
    now[0]=60;r(dict(sim_seconds=720))
    now[0]=90;r(dict(sim_seconds=750))
    now[0]=120;r(dict(sim_seconds=780))
    assert read(root)['sim_speed']==1
    assert read(root)['speed_window_seconds']==60

def test_evaluation_counts_ticks_with_frozen_training_counter(clock):
    root,now=clock;r=Reporter(root,0)
    now[0]=30;r(dict(phase='learning',sim_seconds=640))
    now[0]=31;r(dict(phase='evaluation'),force=True)
    assert read(root)['sim_speed'] is None
    for t in (61,91,121,151):
        now[0]=t;r.advance_simulation(360);r(dict(phase='evaluation'))
        assert read(root)['sim_speed']==12
        assert read(root)['sim_seconds']==640
        assert read(root)['speed_phase']=='evaluation'
    assert read(root)['evaluation_sim_seconds']==1440
    now[0]=181;r(dict(phase='learning',sim_seconds=640))
    assert read(root)['sim_speed'] is None
    now[0]=211;r(dict(sim_seconds=940))
    assert read(root)['sim_speed']==10

def test_stall_stop_reset_and_irregular_sampling(clock):
    root,now=clock;r=Reporter(root,0)
    now[0]=40;r(dict(phase='learning',sim_seconds=400))
    now[0]=80;r(dict(sim_seconds=600))
    assert read(root)['sim_speed']==pytest.approx(6.7)
    now[0]=140;r(dict(sim_seconds=600))
    assert read(root)['sim_speed']==0
    now[0]=170;r(dict(sim_seconds=0))
    assert read(root)['sim_speed'] is None
    now[0]=200;r(dict(phase='stopped'))
    assert read(root)['sim_speed'] is None
    with pytest.raises(ValueError):r.advance_simulation(-10)

def test_mission_evaluation_reports_actual_ticks_without_affecting_game():
    from learning.mission_evaluate import play
    class Progress:
        def __init__(self):self.seconds=0;self.calls=0
        def advance_simulation(self,seconds):self.seconds+=seconds
        def __call__(self,phase):assert phase=='evaluation';self.calls+=1
    p=Progress()
    _,a=play(1,'2',progress=p,limit=20)
    _,b=play(1,'2',limit=20)
    assert p.seconds==20 and p.calls==2
    assert a['hash']==b['hash']

def test_legacy_evaluation_counts_completed_game_ticks(clock,monkeypatch):
    from pathlib import Path
    import learning.league_evaluate as evaluation
    from learning.candidate_env import CandidateEnv
    from engine.scenario import create_match
    root,now=clock
    def tiny(seed=0,swap=False):
        w=create_match(seed,swap);w.teams[0].score=100;return w
    class ShortEnv(CandidateEnv):
        def __init__(self,**kwargs):super().__init__(scenario_factory=tiny,decision_seconds=10)
    class Policy:
        def __init__(self,path):self.policy_id=str(path)
        def predict(self,*args):return 64
    monkeypatch.setattr(evaluation,'CandidateEnv',ShortEnv)
    monkeypatch.setattr(evaluation,'CandidatePolicy',Policy)
    monkeypatch.setattr(evaluation,'export',lambda model,path:Path(path).touch())
    reporter=Reporter(root,0)
    def progress(phase):pass
    progress.advance_simulation=reporter.advance_simulation
    state=dict(run='speed-test',completed_games=50,generation=1)
    result=evaluation.evaluate(root,[None,None],state,progress,seeds=[0])
    assert result['complete'] and len(result['results'])==16
    assert reporter.evaluation_sim_seconds==pytest.approx(16*.2)
    evaluation.evaluate(root,[None,None],state,progress,seeds=[0])
    assert reporter.evaluation_sim_seconds==pytest.approx(16*.2)  # resumed cached cases do not count twice
