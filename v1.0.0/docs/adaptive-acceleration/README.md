# T14 adaptive acceleration

Authorized: retain0.2s physics, independent PPOs and T11 gates; CPU quota<=4;
async paired teacher<=2pairs/min; central on-policy inference and64 total tactical
rounds/update; process engines and bounded asynchronous publications/archives.
Latest completed replay is pinned per browser session; every result is retained.

Baseline: `learning.acceleration_benchmark` seed19/24 heuristic rounds,240sim s.
The cProfile run took59.98s (4.00x); this is instrumented, concurrent with the
existing league and is not an unprofiled production throughput estimate.
Observation copies accounted for12.16s; fixed-step execution39.06s. Full profile
and final state hash are in baseline.json. No training models/results were touched.

Stages: baseline -> async teacher/I/O -> adaptive collector/checkpoint -> engine
copy optimization -> viewer/latest publication -> integrated rollout.

Stage2: AsyncTeacher uses one paired in-flight request and a30s wall-clock
admission interval. It freezes observations/candidates/learner routing. Background
I/O has separate publication/archive processes, coalesced status/replay slots,
pinned immutable archive inputs and a2GiB/1GiB-free safety guard. The adaptive
runner will enable these paths; the existing running worker is not hot-patched.
Tests:8 passed (async frozen-pair routing, durable I/O failures/pinning and speed).

Observation optimization: integer terrain rows are detached using list copies,
retaining mutable-list API and world isolation.23 sensing/live/water/flight tests
passed. Identical seed19/commands retained the exact final hash; instrumented
workload59.98s ->45.74s (~1.31x). Concurrent host activity and profiling affect
these numbers; they do not establish a production learning-speed improvement.

Adaptive collector: persistent spawn processes own engines; the coordinator owns
both Torch policies and per-environment actor RNG.64 total HQ rounds share fixed
weights; GAE is computed per(environment,episode,team) before batching. Shrinking
execution slots parks live environments and retains them in atomic checkpoints.
The adaptive-1 runtime adds environments.json.gz; serial runners explicitly
refuse it instead of silently dropping other games. Full recovery verification
checks every engine branch/RNG, and restores the current/initial frozen evaluation
artifacts and ledger. Existing serial checkpoints migrate without actor/optimizer
reset. T11 rollout recognizes both runner modules and retains its validation gate.

Scaling: unprofiled equal-command12-round engine-only tests measured14.17/23.51/
32.53 aggregate sim-seconds/wall-second with1/2/3workers; RSS60/121/182MiB approx
(worker-only KiB figures are authoritative in scaling.json). Process startup,
Torch updates, network and checkpoint overhead are excluded. All hashes match.
This is evidence for process scaling in this workload, not a guaranteed training
rate. The coordinator starts1slot, tests growth after120s and accepts>=5% gains
only after>=60s/two update windows. Quota/memory/CPU-pressure backoff is automatic.

Run legacy: `.venv/bin/python -m learning.accelerated_league --kind legacy --root data/league-v1 --source data/preserved/pre-league-checkpoint-00002090-d95aa585/latest.npz --pilot 200`.
Mission is launched only by the T11 validation pipeline with `--kind mission
--pilot 192`; it requires the current code fingerprint's validated gate.

Final scaling CPU use averaged1.00/1.97/2.91 cores (workers only); Torch/coordinator and I/O are additional and constrained by the shared4-core cgroup budget.

Publications: verified checksum-named replay objects switch index only after
read-back validation; two generations and600s are retained. A delayed older
completion cannot replace a newer one. Browser timeline remains pinned and offers
an explicit new-game button. Status writes also use a shared monotonic timestamp
pointer so a stopped old runner cannot overwrite a newer runner's status.

Validation: Python full suite234passed (457.42s), later focused14passed,
disk-pause3passed, final publication/teacher7passed; counts overlap. JS33passed.
Chromium1440x900 DPR2 and390x844 verified aggregate labels, pinned paused timeline,
new-game offer, screenshots and no page errors. Preview assets were fetched from
the existing allowed t11-multi-mode alias; preview has no Storage secret, so its
asset check is distinct from production API verification.

Live activation: PPO1/PPO2 full policy and optimizer tensors, step counters and
training-world checksum matched the preserved source exactly.Three generation123/
51-game full recovery manifests are remotely verified, and the source local copy
is retained. Production deployment4c7929b0 uses the actual production branch
`dev/v1.0.0`; previous28e58fa5 remains available for rollback. The real Storage
latest replay was migrated byte-for-byte to its checksum object and read back;
production Chromium consumed the real replay and all four public APIs returned200.

Observed evaluation cohort averaged1.01 CPU core over10s and1695MiB summed RSS
(shared pages counted multiple times; PSS unavailable). This is the existing
ordered frozen evaluation, not the parallel PPO collector. NIM is intentionally
not queried during evaluation; new async teacher sample yield is not yet measured
in live training (configured cap2pairs/min, actual availability remains observable).
Remaining costs include combat/visibility, path search, synchronous atomic local
checkpoint serialization and ordered frozen evaluations. PPO worker adaptation
begins after the preserved evaluation; T11 mixed-mode promotion still requires its
engine/migration gates. CPU benchmark speedups do not prove strategic improvement.


Follow-up timing fix: evaluations and initialization now reset the adaptive
throughput measurement window before learning resumes. A two-hour evaluation
cannot dilute the baseline or falsely approve a worker increase. This timing
change and adaptive-runner rollback detection passed10 tests (108.52s), including
multi-process updates, checkpoint restore and phase-window isolation. Models and
the completed diagnostic were retained; T11's new code pin starts a fresh audit.
The fixed50-game evaluation completed; the learner reached generation125 and52
completed training games before its safe timing-fix restart. New NIM supervision
returned2valid pairs out of4attempts; HTTP429 obeyed its60s delay without stopping
PPO. These are small operational observations, not learning-quality claims.
