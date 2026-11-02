# Frozen policy comparison result

Completed: 80/80, 200-game baseline versus frozen 769-game policy, map 2 only. No training/NIM in evaluation.

| Current learner against its historical policy | W | D | L | Win score | Seed bootstrap 95% interval |
|---|---:|---:|---:|---:|---|
| PPO1 | 1 | 0 | 19 | 0.05 | 0.00–0.15 |
| PPO2 | 10 | 0 | 10 | 0.50 | 0.25–0.70 |

These 40 matches compare history directly; another 40 use algorithm opponents. Five independent seeds with crossed team/start assignments do not establish generalization. PPO1 shows regression against its own past policy; PPO2 superiority is not established. This comparison does not assess the subsequent 933-game checkpoint or maps 3/4. Do not claim continual strategic improvement from training volume.

2026-11-02: execution environment retained checkpoint generation2158/933 games, but learner/reporting processes were absent and heartbeat remained dated2026-10-31. Resumed the existing frozen legacy runtime and checkpoint, without applying mixed-map or rotation updates. PPO1 regression warrants diagnosis independently of runtime reactivation.
