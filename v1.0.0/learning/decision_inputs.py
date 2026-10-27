"""One prefix encoding for rollout, demonstration, distillation and evaluation."""
REVISION = 'mission-inputs-2'


def encode(obs, items, selected=(), *, mission=False):
    if mission:
        from .mission_features import vector
    else:
        from .candidate_policy import vector
    values = vector(obs, items)
    values[16] = len(selected) / 4
    denominator = max(1, obs['resources']['supply']) if mission else 2000
    values[17] = sum(c.get('supply_cost', 0) for c in selected) / denominator
    return values
