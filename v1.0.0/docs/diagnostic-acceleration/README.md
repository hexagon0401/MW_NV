# T24 — Diagnostic acceleration and limited operation

The environment was replaced: every saved learner/validation PID was absent. The last persistent audit had26/30 hash-verified matches. Readiness was stalled for about six hours after its last heartbeat; no background CPU task survives a stopped cloud environment.

A map4/seed6/120s cProfile run made542M calls, including30M passability checks. Navigation now avoids repeated enum/bounds work and exactly shortcuts base-terrain segments; specialized vehicle footprint/traffic terrain always retains its overridden passability sampler. A* memoizes only within one synchronous search; no cache is added to the world. TeamMap retains Mapping view/order/membership semantics with direct underlying iteration.

The120s before/after scene has an identical complete state hash. Separate fixed-midgame20s measurements and their scope are in kernel.json; profiler overhead/CPU contention prevents treating one kernel speedup as whole-game throughput. Initial failed optimization candidates were rejected before runtime adoption.

Full matches and recorded journal replay remain mandatory;0.2s ticks, damage, movement and RNG are not skipped. At most3 independent diagnostic processes share4 allocated CPUs. Each case atomically saves simulation/history/RNG/commands and replay index at300s simulation intervals and catches orderly stops. Partial results are merged once; a restarted case resumes its persisted checkpoint. Full diagnostic results and source proofs remain available.

User explicitly approved limited operation on2026-10-28. Release mixed-maps revision2 requires all30 full engine games, exact replay hashes, source/build and verified remote recovery. Policy retention,192-game pilot and fixed evaluations are follow-up checks, never fabricated passes. The initial two migrated policies retain their weights; source initialization does not train or publish matches. The exact canary revision is reserved for Apply after these technical gates. The previous legacy root/runtime is the recovery target.

An applied canary may recover once from an unexpected stopped coordinator. Persistent failure or a confirmed regression schedules audited rollback. Administrator pause and explicitly owned STOP files are respected. Pages still does not execute PPO.
