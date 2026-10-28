# T24 — Diagnostic acceleration and limited operation

The environment was replaced: every saved learner/validation PID was absent. The last persistent audit had26/30 hash-verified matches. Readiness was stalled for about six hours after its last heartbeat; no background CPU task survives a stopped cloud environment.

A map4/seed6/120s cProfile run made542M calls, including30M passability checks. Navigation now avoids repeated enum/bounds work and exactly shortcuts base-terrain segments; specialized vehicle footprint/traffic terrain always retains its overridden passability sampler. A* memoizes only within one synchronous search; no cache is added to the world. TeamMap retains Mapping view/order/membership semantics with direct underlying iteration.

The120s before/after scene has an identical complete state hash. Separate fixed-midgame20s measurements and their scope are in kernel.json; profiler overhead/CPU contention prevents treating one kernel speedup as whole-game throughput. Initial failed optimization candidates were rejected before runtime adoption.

Full matches and recorded journal replay remain mandatory;0.2s ticks, damage, movement and RNG are not skipped. At most3 independent diagnostic processes share4 allocated CPUs. Each case atomically saves simulation/history/RNG/commands and replay index at300s simulation intervals and catches orderly stops. Partial results are merged once; a restarted case resumes its persisted checkpoint. Full diagnostic results and source proofs remain available.

User explicitly approved limited operation on2026-10-28. Release mixed-maps revision2 requires all30 full engine games, exact replay hashes, source/build and verified remote recovery. Policy retention,192-game pilot and fixed evaluations are follow-up checks, never fabricated passes. The initial two migrated policies retain their weights; source initialization does not train or publish matches. The exact canary revision is reserved for Apply after these technical gates. The previous legacy root/runtime is the recovery target.

An applied canary may recover once from an unexpected stopped coordinator. Persistent failure or a confirmed regression schedules audited rollback. Administrator pause and explicitly owned STOP files are respected. Pages still does not execute PPO.

The latest source pair is generation476 /200 completed legacy matches, archived and loaded remotely before migration. Distillation links each successor to its own current source; original legacy checkpoints and the older migration are preserved. Partial diagnostic snapshots were revalidated with identical world/RNG checksums when the semantics-preserving optimizer was adopted. Only this exact revision2 has an automatic Apply reservation.

A real fixed-Pages-artifact preview caught an unresolved jose dependency in the raw-function snapshot. Pages staging now bundles server dependencies into a hashed dist/_worker.js before registration; isolated deploys require no mutable node_modules. The failed artifact remains preserved and a new content revision is used.

The cloud-environment-onboarding setup skill was used to correct obsolete startup instructions (which still named the non-adaptive legacy runner). The start_skill draft was saved; it does not publish the environment or keep processes alive after shutdown. Environment settings must be reviewed/saved and Published to activate that reusable snapshot.

Real Pages Apply completed through the registry/phase journal (canary-status-ui revision4, production9e6aa519; rollback39dc74b5). Production marker/API, strict CSP and desktop/mobile Chromium were checked. Missing dependencies and an incompatible multipart-worker packaging candidate were rejected in preview; directory Worker plus separately archived function sources now deploys without a live node_modules dependency.

After an environment restart, dashboard collection now verifies the registered learner PID/start/module before showing its old evaluation as active. An absent learner reports offline/zero PPO slots/unknown throughput while preserving its200 completed games. Diagnostic parents and future active release roots are included in resource process accounting. Replay validation is shown in the release panel separately from running matches.

Final checks:325 full-suite tests at the implementation snapshot,38 later targeted tests and31 controller/liveness checks (overlap);56 JS tests/build; actual production browser and typed Pages Apply. The runtime/mixed-model promotion has not yet executed; revision2 remains reserved until all30 hashes/source recovery pass. A later optional request to start with26 completed games is still unanswered, so the30-game prerequisite is unchanged.
