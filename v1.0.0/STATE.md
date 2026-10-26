# MW-NV v1.0.0 STATE
Current:T14 stage2 async teacher/durable I/O COMPLETE;adaptive collector in progress
Read:docs/adaptive-acceleration/README.md;docs/speed-reporting/README.md
Cause:evaluation wall time grew while numerator stayed at640 training seconds
Fix:recent60s phase speed;actual evaluation ticks;NIM network/5xx backoff60..300s
Verified:T13 regression29;T14 async/I/O/speed8passed;baseline seed19/240sim s
Runtime:league-v1 PID118450 resumed generation122/50games;remote recovery verified
Check:data/league-v1/training-status.json and runner.pid;do not duplicate worker
T11:telemetry-only validation fingerprint refreshed;engine rules/geometry unchanged
T11:old13 pre-flight-fix diagnostics retained in validation-before-heli
T11 resume waits for legacy50-game evaluation completion to share2CPU budget
Check:data/multi-mode-v1/rollout-status.json and heli-validation-resume.pid/rollout.pid
Site:https://mw-nv.pages.dev production28e58fa5;no frontend deployment needed
No actual throughput improvement claim;Mac/permanent CPU unverified
Usage:UNKNOWN
