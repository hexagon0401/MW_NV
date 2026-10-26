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
