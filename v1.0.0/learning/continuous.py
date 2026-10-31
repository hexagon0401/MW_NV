"""User-started CPU training rounds, immutable checkpoints and resumable journal."""
import argparse
import json
from pathlib import Path
from .train import train


def prune_checkpoints(root,index):
    for path in Path(root).glob('round-*.*'):
        number=int(path.stem.split('-')[1])
        if number<index-7 and number%100!=0:path.unlink()


def run(root='data/continuous', rounds=1, steps=256,contract='tactics'):
    if contract not in ('tactics','legacy'):raise ValueError('contract')
    if contract=='tactics':
        from .candidate_train import train as train_round
    else:train_round=train
    if rounds<0 or steps<64:raise ValueError('rounds >= 0, steps >= 64 required')
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    indices=[int(p.stem.split('-')[1]) for p in root.glob('round-*.npz')]
    index=max(indices,default=-1)+1
    if index and contract=='tactics':
        from .candidate_policy import CandidatePolicy
        CandidatePolicy(root/f'round-{index-1:06d}.npz')
    completed=0
    historical=json.loads((root/"state.json").read_text()).get("total_steps") if (root/"state.json").exists() else None
    if historical is None:historical=sum(json.loads(p.read_text()).get("steps",0) for p in root.glob("round-*.json"))
    try:
        while rounds==0 or completed<rounds:
            name=root/f'round-{index:06d}'
            opponent_index=max(0,index-(4 if index%4==2 else 1))
            opponent=str(root/f'round-{opponent_index:06d}.npz') if index and index%4 else None
            staged=root/'.pending'/name.name
            if contract=='tactics':
                from .training_status import Reporter
                report=Reporter(root,index,historical);report(dict(phase='learning',round_steps=steps),force=True)
                train_round(staged,steps,'A' if index%2==0 else 'B',opponent,index,resume=str(root/f'round-{index-1:06d}.zip') if index else None,progress=report)
            else:train_round(staged,steps,'A' if index%2==0 else 'B',opponent,index)
            # Publish the NumPy file last: its presence marks a complete round.
            for suffix in (('.zip','.json','.npz') if contract=='tactics' else ('.zip','.npz')):staged.with_suffix(suffix).replace(name.with_suffix(suffix))
            historical+=steps
            if contract=='tactics':
                report.base_steps=historical;report(dict(phase='checkpoint_saved',checkpoint=name.name),force=True)
            record=dict(contract=contract,round=index,total_steps=historical,steps=steps,policy=str(name.with_suffix('.npz')),opponent=opponent,selected=False)
            temporary=root/'state.partial';temporary.write_text(json.dumps(record,indent=2)+'\n');temporary.replace(root/'state.json')
            prune_checkpoints(root,index)
            print(json.dumps(record),flush=True)
            index+=1;completed+=1
    except KeyboardInterrupt:
        print('Stopped; completed rounds retained. Resume with the same command.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='data/continuous');p.add_argument('--rounds',type=int,default=1,help='0 repeats until Ctrl+C');p.add_argument('--steps',type=int,default=256);p.add_argument('--contract',choices=['tactics','legacy'],default='tactics');a=p.parse_args();run(a.root,a.rounds,a.steps,a.contract)
