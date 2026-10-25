# MW-NV v1.0.0 STATE
Current: T02 live training report, unpaced PPO, normal-speed replay, map transfer preparation
Status: implemented/deployed; continuous CPU PPO resumed with prior weights+optimizer
Site: https://mw-nv.pages.dev; latest training replay ?match=training-latest
Deploy: https://22caad51.mw-nv.pages.dev; public viewer; Supabase private objects
UI: /api/training every30s; steps/round/sim-speed/CPU/time; stale report marked
Training: rounds0/steps256; data/nim-approved-training; runner.pid / runner-v2.log
Resume: .zip weights/optimizer; mixed opponents; retain latest8 +100-round milestones
Maps: four geometry/cover variants, injected scenario factory; train0–49/eval10000–10099
Replay: latest completed only, gzip/checksum/one object; original ticks/default1x
Verified: training+tactics9 +retention1; JS15; build/Functions; desktop/mobile Chromium
Verified: round9 policy_steps512 resumed round8; remote training200/list contains training-latest
Baseline transfer: old policy0/2 wins on held-out mirrored seed; no improvement claim
Next: continue training; paired held-out evaluations before promoting any policy
Limits: Codex environment may stop; NIM unused in PPO; arbitrary new maps unproven; usage UNKNOWN
