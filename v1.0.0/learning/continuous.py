"""User-started CPU training rounds, immutable checkpoints and resumable journal."""
import argparse
import json
from pathlib import Path
from .train import train


def run(root='data/continuous', rounds=1, steps=256):
    if rounds<0 or steps<64:raise ValueError('rounds >= 0, steps >= 64 required')
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    index=0
    while (root/f'round-{index:06d}.npz').exists():index+=1
    completed=0
    try:
        while rounds==0 or completed<rounds:
            name=root/f'round-{index:06d}'
            opponent=str(root/f'round-{index-1:06d}.npz') if index else None
            staged=root/'.pending'/name.name
            train(staged,steps,'A' if index%2==0 else 'B',opponent,index)
            # Publish the NumPy file last: its presence marks a complete round.
            for suffix in ('.zip','.npz'):staged.with_suffix(suffix).replace(name.with_suffix(suffix))
            record=dict(round=index,steps=steps,policy=str(name.with_suffix('.npz')),opponent=opponent,selected=False)
            temporary=root/'state.partial';temporary.write_text(json.dumps(record,indent=2)+'\n');temporary.replace(root/'state.json')
            print(json.dumps(record),flush=True)
            index+=1;completed+=1
    except KeyboardInterrupt:
        print('Stopped; completed rounds retained. Resume with the same command.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='data/continuous');p.add_argument('--rounds',type=int,default=1,help='0 repeats until Ctrl+C');p.add_argument('--steps',type=int,default=256);a=p.parse_args();run(a.root,a.rounds,a.steps)
