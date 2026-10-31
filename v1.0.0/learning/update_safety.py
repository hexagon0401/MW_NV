"""Bounded auxiliary imitation; rollback never undoes the preceding PPO update."""
from collections import Counter
from copy import deepcopy
import numpy as np
import torch


def imitate(model, rows, stats, max_kl=.02):
    if not rows:
        return None
    obs = torch.as_tensor(np.stack([r[0] for r in rows]), device=model.device)
    actions = torch.as_tensor([r[2] for r in rows], device=model.device)
    masks = np.stack([r[1] for r in rows])
    if not np.isfinite(obs.cpu().numpy()).all() or not all(m[a] for m, a in zip(masks, actions.cpu().numpy())):
        raise ValueError('invalid imitation sample')
    weights = deepcopy(model.policy.state_dict())
    optimizer = deepcopy(model.policy.optimizer.state_dict())
    with torch.no_grad():
        old = model.policy.get_distribution(obs, action_masks=masks).distribution.probs.detach().clone()
    _, logp, _ = model.policy.evaluate_actions(obs, actions, action_masks=masks)
    loss = -.05 * logp.mean()
    model.policy.optimizer.zero_grad()
    loss.backward()
    norm = torch.nn.utils.clip_grad_norm_(model.policy.parameters(), .5)
    model.policy.optimizer.step()
    finite = all(bool(torch.isfinite(p).all()) for p in model.policy.parameters())
    kl = torch.tensor(float('nan'))
    if finite:
        with torch.no_grad():
            new = model.policy.get_distribution(obs, action_masks=masks).distribution.probs
            kl = (old * (old.clamp_min(1e-30).log() - new.clamp_min(1e-30).log())).sum(-1).mean()
            finite = bool(torch.isfinite(kl))
    stats['last_imitation_kl'] = float(kl) if torch.isfinite(kl) else None
    stats['last_gradient_norm'] = float(norm) if torch.isfinite(norm) else None
    stats['last_sample_counts'] = {key: dict(Counter(str((r[4] if len(r)>4 else {}).get(key, 'unknown')) for r in rows)) for key in ('mode', 'stage')}
    stats['last_sample_teams'] = dict(Counter(str(r[3]) for r in rows))
    if not finite or not torch.isfinite(norm) or float(kl) > max_kl:
        model.policy.load_state_dict(weights)
        model.policy.optimizer.load_state_dict(optimizer)
        stats['imitation_rollbacks'] = stats.get('imitation_rollbacks', 0) + 1
        return None
    stats['imitation_updates'] = stats.get('imitation_updates', 0) + 1
    stats['last_imitation_loss'] = float(loss.detach())
    return stats['last_imitation_loss']
