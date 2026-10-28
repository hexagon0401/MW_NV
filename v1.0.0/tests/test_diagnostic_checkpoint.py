import pytest
from engine.runtime import Engine
from engine.replay import RecordingEngine
from engine.state import WorldState
from learning.diagnostic_checkpoint import DiagnosticCheckpoint
from learning.validation_progress import replay


def test_interrupted_simulation_preserves_world_rng_history_and_recorded_commands(tmp_path):
    e=RecordingEngine(WorldState(42));e.step(2)
    cp=DiagnosticCheckpoint(tmp_path,'2:42:0');cp.save_simulation(e,{0:[.2,.4],1:[.1]},3,force=True)
    loaded,history,decisions=DiagnosticCheckpoint(tmp_path,'2:42:0').restore_simulation()
    assert history=={0:[.2,.4],1:[.1]} and decisions==3
    assert loaded.document()==e.document()
    loaded.step(2);e.step(2);assert loaded.world.checksum()==e.world.checksum()


def test_interrupted_replay_resumes_exact_journal_index(tmp_path):
    e=RecordingEngine(WorldState(42))
    for _ in range(3):e.step(2)
    class Progress:
        def __init__(self,interrupt):self.checkpoint=DiagnosticCheckpoint(tmp_path,'2:42:0');self.interrupt=interrupt
        def write(self,**kw):pass
        def __call__(self,*args):
            if self.interrupt:raise InterruptedError()
    with pytest.raises(InterruptedError):replay(e.document(),Progress(True))
    saved=Progress(False).checkpoint.load('replay');assert saved['index']==1
    assert replay(e.document(),Progress(False)).checksum()==e.world.checksum()


def test_checkpoint_dependency_mismatch_is_not_silently_resumed(tmp_path):
    cp=DiagnosticCheckpoint(tmp_path,'2:42:0');cp.save_simulation(RecordingEngine(WorldState(42)),{0:[],1:[]},0,force=True)
    cp.identity='changed'
    with pytest.raises(ValueError,match='dependencies changed'):cp.restore_simulation()
