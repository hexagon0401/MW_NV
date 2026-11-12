# T13 backend speed reporting

The legacy league reported training-only simulated seconds divided by total runner
wall time. At 50 completed games, `sim_seconds` stayed at 640 during frozen
evaluation; the displayed speed fell from 0.5x to 0.3x while evaluation completion
advanced from 13 to 18 of 80. A sampled worker interval consumed 100% of one CPU.
This demonstrates a reporting error, not evidence of a measured performance regression.
No before/after engine throughput improvement is claimed.

Reporter now computes simulation seconds / wall seconds over the latest 60 seconds
(with linear interpolation at the window boundary). Training and evaluation have
separate counters; phase transitions discard the previous phase's timing window.
Legacy and multi-mode evaluators count actual advanced ticks, including short final
ticks, without changing engine state. Resumed/skipped completed cases are not counted
again. A new phase reports null until a measured interval exists, and stopped workers
report null. The existing viewer renders null as an em dash. Communication, policy
inference, and bookkeeping inside the measured interval remain part of elapsed time.
No forced speed cap, physics/RNG change, or model reset was introduced.

NIM request timeouts can also reduce actual training throughput. The resumed worker
reported 1.2x over its first 40.6s and later 3.7x over a full 60s; these are distinct
from the old broken evaluation ratio. These samples include concurrent diagnostic tests and are not a performance benchmark. A live HTTP 429 was observed and its existing
Retry-After cooldown is preserved. Historical last_error=TimeoutError alone does
not timestamp a new timeout. Added network/5xx failure backoff of 60/120/240/300s
(max 300), resetting after a valid paired response. During cooldown PPO proceeds
without either team's teacher labels. This does not bypass rate limits or alter
the 30s simulation teacher cadence when available. Request duration/retry delay
are exposed in the existing teacher status object. No live NIM recovery claim.

Validation: 29 tests passed in 62.87s; see verification.json. Cases
cover rolling-window speeds, phase changes, stalls/stops, exact evaluation ticks,
resumed/skipped cases, transport-independent game hash equality, network backoff,
paired teacher recovery, Retry-After, independent PPO update and checkpoint resume.

Deployment: engine worker PID118450 resumed generation122 / 50 games after full recovery archive verification (pending queue empty). Live status confirms the new speed basis.
Completed frozen evaluation cases and the original checkpoint files are preserved.
The incomplete evaluation case may be replayed; the existing coordinator resumes
its normal update/evaluation schedule. No frontend deployment is required.
T11's validation fingerprint was refreshed for telemetry-only changes; engine
rules and geometry are unchanged. Existing pre-flight-fix diagnostics remain separate.
