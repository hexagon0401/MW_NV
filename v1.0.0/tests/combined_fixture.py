"""Real release runner for combined-arms browser checks; never alters production balance."""
import os,shutil,tempfile
from pathlib import Path
from engine.replay import RecordingEngine
from engine.scenario import create_release_match
from server.live import LiveRunner,serve

root=Path(__file__).resolve().parents[1]
ending=bool(os.environ.get('MW_NV_END_TEST'));out=Path(tempfile.mkdtemp(prefix='mw-nv-end-')) if ending else root/'data/combined-browser';out.mkdir(parents=True,exist_ok=True)
if not ending and (root/'data/ca-final-verification/paired-teams.sqlite').exists():shutil.copy2(root/'data/ca-final-verification/paired-teams.sqlite',out/'results.sqlite')
world=create_release_match(17)
if ending:world.tick=14990
runner=LiveRunner(RecordingEngine(world),output_dir=out)
try:serve(runner,port=int(os.environ['MW_NV_TEST_PORT']),log_level='warning')
finally:
    if ending:shutil.rmtree(out)
