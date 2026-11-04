# MW-NV v1.0.0 STATE
Current:T29 runtime continuity IMPLEMENTED;Cloudflare activation blocked until Publish/free setup
Tests:Python22 PASS(including actual lease-expired PPO no-update);JS65/build PASS;preview desktop/mobile PASS
Backup:current mixed18games/g60 full verified training-2026-11-005;isolated download/restore in progress
Code:runtime-continuity r2 immutable source863b510e;remote code archive verify in progress
Monitoring:D1 read401/account+subscriptions403;user entered new token but it applies after session-end Publish
Safety:no Worker/D1/Cron created;no managed learner launched without lease;models/rotation unchanged
Config:start_skill/bootstrap and MW_NV_RUNTIME_MONITOR_KEY requirement saved(draft;requires Publish)
Secrets:data/runtime/monitor.key mode600;NEVER print/commit;user must persist same raw key in env
Read:docs/runtime-continuity.md
Next:finish cold restore/code proof→register BLOCKED public card→finish observability UI Apply→push
After Publish:confirm Workers Free/D1 auth→deploy_runtime_monitor --confirm-free→prepare_runtime_release→typed Apply
Usage:UNKNOWN
