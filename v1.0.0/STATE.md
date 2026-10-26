# MW-NV v1.0.0 STATE
Current:T14 adaptive collector/atomic recovery COMPLETE;viewer rollout/switch in progress
Read:docs/adaptive-acceleration/README.md;docs/speed-reporting/README.md
Cause:evaluation wall time grew while numerator stayed at640 training seconds
Fix:recent60s phase speed;actual evaluation ticks;NIM network/5xx backoff60..300s
Verified:Python234+focused14;JS33;Chromium desktop/mobile;engine scaling hashes equal
Runtime:legacy safely stopped gen123/51games;pre-adaptive local copy retained
Check:data/league-v1/training-status.json and runner.pid;do not duplicate worker
T11:telemetry-only validation fingerprint refreshed;engine rules/geometry unchanged
T11:old13 pre-flight-fix diagnostics retained in validation-before-heli
T11 gate retained;resume canonical50-game frozen evaluation before parallel learning
Check:data/multi-mode-v1/rollout-status.json and heli-validation-resume.pid/rollout.pid
Site:https://mw-nv.pages.dev production28e58fa5;no frontend deployment needed
No actual throughput improvement claim;Mac/permanent CPU unverified
Usage:UNKNOWN
