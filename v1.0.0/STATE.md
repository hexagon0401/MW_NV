# MW-NV v1.0.0 STATE
Current:T11 stages1-6 implemented/deployed;stage7 long-run validation/pilot IN PROGRESS
Read:docs/multi-mode/{PLAN,README,STATUS}.md;do not restart or replace live workers blindly
Engine:opt-in rules5/catalog3;96inf+16vehicles;air/AA/crews;finite attrition;physical flag missions
Policy:tactics3/1600x65;independent PPO1/PPO2 across3modes;separate old-actor distillation
Verified:Python full202+final scoped14+rollback2;web31;60geometry seeds;Chromium DPR1/2/mobile
Evidence:docs/multi-mode/{validation,browser,performance,source-archive,deployment}.json
Site:https://mw-nv.pages.dev production28e58fa5;actual replay/history/filters/Storage200 verified
Rollback:previous productionbdd8e560;preview backend lacks secret,frontend test bridge documented
Runtime:legacy league-v1 retained;new rollout audit running;2/30full-game hashes verified last read
Gate:30diagnostics+map2 old/new retention before switch;then192mixed pilot+96game mode evaluations
Resume:read data/multi-mode-v1/rollout-status.json and verify matching rollout.pid before launching
Command:.venv/bin/python -m learning.mission_rollout --root data/multi-mode-v1 --legacy data/league-v1
Backup:10games/24updates policies;50games/120updates full;immutable verified Releases
No proven strategic improvement/transfer;500units≈12fps SwiftShader;Mac/permanentCPU unverified
Usage:UNKNOWN
