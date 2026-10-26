# MW-NV v1.0.0 STATE
Current:T12 helicopter interrupted-flight fix COMPLETE;T11 validation continues separately
Read:docs/heli-interruption/README.md;docs/multi-mode/STATUS.md
Cause:airborne command cancellation set READY over water;165 LANDING_INVALID in latest replay
Fix:preserve HOVERING;recover journal-backed legacy states;no airborne boarding/unloading
Verified:40 transport/air/combat/replay/checkpoint/PPO tests;both teams;HEL/BH/LB;hash match
Preserved:league-v1 generation120/50games full recovery remotely verified;models/statistics retained
Runtime:resume same league-v1 checkpoint with fixed engine;do not duplicate matching runner.pid
T11:old13 diagnostics preserved in data/multi-mode-v1/validation-before-heli;rerun on fixed engine
T11 resume waits for legacy50-game evaluation completion to share2CPU budget
Check:data/multi-mode-v1/rollout-status.json and heli-validation-resume.pid/rollout.pid
Site:https://mw-nv.pages.dev production28e58fa5;no UI deployment required for engine fix
Old completed replays unchanged;new/restarted games use fixed flight logic
No strategy-improvement claim;Mac/permanent CPU unverified
Usage:UNKNOWN
