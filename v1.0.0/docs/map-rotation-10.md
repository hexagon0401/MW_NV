# 10-completed-game map rotation — registered update

Release ID: `map-rotation-10`, revision 2. READY after tests and remote candidate recovery verification; user explicitly authorized immediate Apply. Auto-apply remains off.

- Repeat map 3 (annihilation) → map 4 (CTF) → map 2 (capture), 10 completed training games per map.
- Preserve PPO1/PPO2; never split policies by map. Alternate teams/start assignments and preserve long-run historical/algorithm opponent proportions. Ten is not divisible by the existing 32-case role cycle, so fairness carries across visits rather than resetting the role sequence every ten games.
- Count unique completed training matches only. Evaluation, diagnostics, NIM demonstrations, aborted and duplicate games do not advance the counter.
- Parallel allocation must reserve at most the remaining quota, drain the current map's batch before issuing the next, and persist reservations/IDs/completion counts. Never swap the map inside an active match.
- Persist current map, batch, completed IDs, assignment and role cursors across checkpoints/restart. Respect existing administrator pause state.
- Apply at a safe update boundary, retaining models/optimizers/RNG/statistics and a verified rollback target. Existing runs never change merely because the manifest is registered.

Gates: implement scheduler/handler; check 9→10→next-map boundaries, duplicate/abort handling, parallel out-of-order completions and all three map visits; checkpoint resume equivalence; long-run team/start/opponent balance; isolated integration and rollback.

Revision2 supersedes the rolled-back mixed release; engine source matches its validated30-game engine exactly. Serial collection enforces the ten-completion barrier and retains existing role allocation. The earlier demonstration subprocess timeout is avoided by disabling demonstration coaching only; ordinary async NIM stays enabled. Integration smoke actually updated both policies on map3 and resumed a checkpoint. Tests:21 rotation/release plus13 adaptive/mission/watch tests passed.

Starting policies are separately distilled from the preserved1189-game/g2748 capture specialists (see capture-baseline-1189.md), not the old18-game mixed source used only in the integration smoke. New input semantics require fresh critic/optimizer. Initial KL of distillation and behavior retention are not proof of strategic improvement. Full capture recovery and separate A′/B′ Release remain preserved. Current new-rule performance remains unverified.
