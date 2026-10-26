# MW-NV v1.0.0 STATE
Current: T08 objective first-capture analytics COMPLETE; T07 larger repair plan still pending
Site: https://mw-nv.pages.dev; deployment https://aea6b716.mw-nv.pages.dev
Recorded: first team/time, loss vs enemy retake, recovery, hold duration, opening/order, control checkpoints
Context: score/army at first capture; north/center/south combinations; filters by mode/rules/map/policy/side
Storage: additive objective_stats in match JSON/SQLite/export; legacy missing values remain unknown
Verified: targeted Python14 (+training enhance suite17 earlier), JS24, build/Functions, Chromium desktop/mobile
Remote: /api/objectives HTTP200; actual new training match collected/published; page errors0
Evidence: docs/objective-statistics/README.md, production.json and fixture/deployed screenshots
Training: self-play-v3 safely resumed from gen1869; observed gen1876/681games/120064steps
Recovery: inspect PID first; .venv/bin/python -m learning.self_play --root data/self-play-v3 --seed-policy data/self-play-v3/seed.zip
Models: cutover checkpoints pinned in ignored data/preserved; remote Release backup still unverified
Next: implement docs/learning-repair-plan.md (archive/fair scheduling/movement/discovery); no claims completed
Caution: first-capture win rate is association; count/draws/conditions visible; no causal claim
Limits: no permanent external CPU; Intel Mac/performance improvement unverified; usage UNKNOWN
