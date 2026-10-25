# MW-NV v1.0.0 STATE
Current: T04 completed-results dialog + readable tactical commands + free-host investigation
Status: implemented/tested/deployed; permanent external CPU NOT provisioned
Site: https://mw-nv.pages.dev; deployment 9ee26e3a; default latest completed training replay
History: all recorded completed modes; /api/stats + /api/history?offset=0; 50-row pages
UI: named squad/vehicle badges; command/goal/phase cards; actual-shot combat markers
Engine: presentation telemetry outside World hash; original physics/events preserved
Verified: Python23, JS21, production/Functions builds, Chromium desktop/mobile/history
Remote: stats/history/training HTTP200; observed72 results A34/B38; pages50+22
Training: data/self-play-v2 runner.pid; observed gen109,40 completed games,13632 policy steps
Recovery: .venv/bin/python -m learning.self_play --root data/self-play-v2 --seed-policy data/self-play-v2/seed.zip
Blocker: Release uploads.github.com forbidden; local checkpoints kept; no verified remote model backup
Hosting: Oracle official docs CONNECT403; docs.oracle.com/www.oracle.com draft needs Save/Publish
Next: verify free-host terms/account/capacity after network change; ops/ALWAYS_ON.md service template
Details: docs/command-clarity/REPORT.md; Intel Mac/strategy improvement unverified; usage UNKNOWN
