# MW-NV v1.0.0 STATE
Current: T05 COMPLETE; final tactical UI deployed and public site verified 2026-10-26 KST
Site: https://mw-nv.pages.dev; production https://aac65376.mw-nv.pages.dev
Verified: prior Python150+safety1; today JS22, production/Functions build
Remote: HTML/JS hash match; stats/history/training/latest replay HTTP200; Chromium fonts/history PASS
Replay: rules3/catalog2/river-districts v2;148 initial units; completed latest training match
Games: final10 A5/B5; deterministic rerun PASS; west8/east2; BLOCKED/TRAFFIC_TIMEOUT remain
Evidence: docs/tactical-redesign/REPORT.md, GAMES.md, production.json, deployed.png
Training: existing self-play-v3 worker20442 retained; observed650 games/114752steps; evaluation phase
Recovery: inspect PID first; .venv/bin/python -m learning.self_play --root data/self-play-v3 --seed-policy data/self-play-v3/seed.zip
Legacy: self-play-v2 rules2 checkpointgen256/games93/steps23040 preserved; never resume as rules3
Blocker: Release uploads deferred; local recovery kept; no verified remote model backup
Startup: v3 environment draft saved but needs user Save/Publish; no permanent external CPU
Next: separate traffic/formation arrival diagnosis and larger paired-side evaluation; PR1 updated
Limits: Intel Mac/performance improvement unverified; usage UNKNOWN
