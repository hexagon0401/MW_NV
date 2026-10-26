# MW-NV v1.0.0 STATE
Current:T13 backend speed reporting fixed;T12 helicopter fix retained
Read:docs/speed-reporting/README.md;docs/heli-interruption/README.md
Cause:evaluation wall time grew while numerator stayed at640 training seconds
Fix:recent60s phase speed;actual evaluation ticks;NIM network/5xx backoff60..300s
Verified:29 focused regression tests passed;game hash unchanged;Retry-After retained
Runtime:league-v1 PID118450 resumed generation122/50games;remote recovery verified
Check:data/league-v1/training-status.json and runner.pid;do not duplicate worker
T11:telemetry-only validation fingerprint refreshed;engine rules/geometry unchanged
T11:old13 pre-flight-fix diagnostics retained in validation-before-heli
T11 resume waits for legacy50-game evaluation completion to share2CPU budget
Check:data/multi-mode-v1/rollout-status.json and heli-validation-resume.pid/rollout.pid
Site:https://mw-nv.pages.dev production28e58fa5;no frontend deployment needed
No actual throughput improvement claim;Mac/permanent CPU unverified
Usage:UNKNOWN
