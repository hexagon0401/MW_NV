"""Sequential frozen-opponent pool; checkpoints never overwrite earlier policies."""
import json
from pathlib import Path
from .train import train


def run(root='data/policies',steps=256):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if not (root/'policy0.npz').exists():train(root/'policy0',steps)
    for generation,controlled in [(1,'B'),(2,'A')]:
        if (root/f'policy{generation}.npz').exists():raise ValueError('checkpoint exists; select a new output directory')
        train(root/f'policy{generation}',steps,controlled,str(root/f'policy{generation-1}.npz'),generation)
        print(f'policy{generation} trained as {controlled} against frozen policy{generation-1}',flush=True)
    manifest=dict(training_seed_range=[0,49],holdout_seed_range=[10000,10099],steps_per_generation=steps,policies=[dict(id=f'policy{i}',controlled='B' if i==1 else 'A',path=str(root/f'policy{i}.npz')) for i in range(3)],best='rules',selection='retain rules until held-out evaluation demonstrates improvement')
    (root/'pool.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':run()
