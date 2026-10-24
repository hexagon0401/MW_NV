# Held-out evaluation

Training seeds: 0–49. Baselines: 1000–1049. Holdout: 10000–10099.

| Policy | Opponent | Games | A wins | Draws | Mean score difference | Invalid actions |
|---|---|---:|---:|---:|---:|---:|
| data/policies/policy0.npz | rules | 100 | 2 | 0 | -81.68 | 0 |
| data/policies/policy2.npz | data/policies/policy0.npz | 10 | 8 | 0 | -1.70 | 0 |
| data/policies/policy2.npz | data/policies/policy1.npz | 10 | 0 | 0 | -5.00 | 0 |
| data/policies/policy2.npz | rules | 100 | 0 | 0 | -5.00 | 0 |
| rules | rules | 100 | 50 | 21 | 21.27 | 0 |

Each policy receives one squad/goal action per HQ round. No LLM calls.
These are small CPU training runs; no policy improvement is assumed.
Detailed losses, supply remaining and measured wall time are in the CSV/JSON.
