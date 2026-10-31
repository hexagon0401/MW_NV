# 10-completed-game map rotation — registered update

Release ID: `map-rotation-10`, revision 1. PLANNED, manual Apply only; no operational change or authorization to auto-apply. This is an upcoming update entry, not a validated ready-to-run artifact.

- Repeat map 2 (capture) → map 3 (annihilation) → map 4 (CTF), 10 completed training games per map.
- Preserve PPO1/PPO2; never split policies by map. Alternate teams/start assignments and preserve long-run historical/algorithm opponent proportions. Ten is not divisible by the existing 32-case role cycle, so fairness carries across visits rather than resetting the role sequence every ten games.
- Count unique completed training matches only. Evaluation, diagnostics, NIM demonstrations, aborted and duplicate games do not advance the counter.
- Parallel allocation must reserve at most the remaining quota, drain the current map's batch before issuing the next, and persist reservations/IDs/completion counts. Never swap the map inside an active match.
- Persist current map, batch, completed IDs, assignment and role cursors across checkpoints/restart. Respect existing administrator pause state.
- Apply at a safe update boundary, retaining models/optimizers/RNG/statistics and a verified rollback target. Existing runs never change merely because the manifest is registered.

Gates: implement scheduler/handler; check 9→10→next-map boundaries, duplicate/abort handling, parallel out-of-order completions and all three map visits; checkpoint resume equivalence; long-run team/start/opponent balance; isolated integration and rollback.

Dependency: mixed-map release must be operational again. At registration `mixed-maps` was ROLLED_BACK, so this entry stays PLANNED, auto=false and Apply locked. A later implementation must register a new immutable revision with verified artifacts before READY. No map 5 is added.
