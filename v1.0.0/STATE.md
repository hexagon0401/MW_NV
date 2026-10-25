# MW-NV v1.0.0 STATE
Current: T05 WIP saved at user request; development paused
Done: compact icons/selection/follow, district map/art, rules3 tank splash/VFX, actor migration
Verified: Python150 + safety1; JS22; Vite/Functions; Chromium mobile/500 units20FPS SW
Games: final10 complete A5/B5; deterministic reexecution PASS; west8/east2; traffic failures remain
Evidence: docs/tactical-redesign/REPORT.md, GAMES.md, screenshots and games.json
Production: https://mw-nv.pages.dev deployment6af5b1f9 (earlier build); remote verification PENDING
Pending: final tested UI polish NOT deployed; preview CF success but preview GET CONNECT403
Training: self-play-v3 worker20442 kept running per continuous-training authorization
Observed: generation36,13 completed new games,2304steps; paired teacher34; no improvement claim
Legacy: self-play-v2 checkpointgen256/games93/steps23040 preserved; rules2 cannot resume on rules3
Recovery: .venv/bin/python -m learning.self_play --root data/self-play-v3 --seed-policy data/self-play-v3/seed.zip
Next: inspect PID/state first; deploy final viewer/dist, verify public APIs/new replay, update PR1
Blocker: Release uploads forbidden; local models kept; startup draft v3 saved needs Save/Publish
Limits: no permanent CPU server; Intel Mac unverified; usage UNKNOWN
