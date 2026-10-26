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
