"""Geometry-only audit, no learning or teacher API calls."""
import json,time
from pathlib import Path
from engine.multi_scenario import create

def run():
    output=Path('docs/multi-mode');output.mkdir(exist_ok=True);rows=[];started=time.monotonic()
    for mode in ('3','4'):
        for seed in range(30):
            world=create(seed,scenario_id=mode);rows.append(dict(scenario=mode,seed=seed,**world.generation))
        print('geometry',mode,'30 seeds PASS',flush=True)
        (output/'geometry.json').write_text(json.dumps(dict(complete=False,results=rows),indent=2))
    (output/'geometry.json').write_text(json.dumps(dict(complete=True,seeds_per_mode=30,total_seconds=time.monotonic()-started,results=rows),indent=2))

if __name__=='__main__':run()
