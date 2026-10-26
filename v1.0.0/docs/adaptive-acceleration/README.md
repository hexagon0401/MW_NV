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
