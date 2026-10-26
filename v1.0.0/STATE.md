# MW-NV v1.0.0 STATE
Current:T14 collector/GAE/resume8passed;terrain copy optimization23passed
Read:docs/adaptive-acceleration/README.md;docs/speed-reporting/README.md
Cause:evaluation wall time grew while numerator stayed at640 training seconds
Fix:recent60s phase speed;actual evaluation ticks;NIM network/5xx backoff60..300s
Verified:seed19 baseline/optimized hash equal;profile throughput1.31x;not production claim
Runtime:league-v1 PID118450 resumed generation122/50games;remote recovery verified
Check:data/league-v1/training-status.json and runner.pid;do not duplicate worker
T11:telemetry-only validation fingerprint refreshed;engine rules/geometry unchanged
T11:old13 pre-flight-fix diagnostics retained in validation-before-heli
T11 resume waits for legacy50-game evaluation completion to share2CPU budget
Check:data/multi-mode-v1/rollout-status.json and heli-validation-resume.pid/rollout.pid
Site:https://mw-nv.pages.dev production28e58fa5;no frontend deployment needed
No actual throughput improvement claim;Mac/permanent CPU unverified
Usage:UNKNOWN
