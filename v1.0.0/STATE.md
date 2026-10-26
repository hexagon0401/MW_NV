# MW-NV v1.0.0 STATE
Current: T09 implementation COMPLETE;200game pilot RUNNING (not completed)
Viewer: https://mw-nv.pages.dev production41371462; previewcc07b34f; previous17e65f49 retained
Features: wheel/pinch zoom+drag; real units>=20%; DPR<=2 screen text; tank/artillery origin trails
Movement: rules4 footprint paths/physical column; mirrored bridge tests; reference-route comparisons100 pass
Audit:10games A4/B6 west7/east3; deterministic reexecution PASS; traffic failures remain
Learning: independent PPO1/PPO2;10s tactics/paired30s NIM; initial evaluation1CPU + learning1CPU
Runtime: league-v1 LIVE generation20/7games/7864steps; initial eval33/80
Recovery: data/league-v1/current.json; source data/preserved/pre-league-checkpoint-00002090-d95aa585/latest.npz
Archive: old2090 and new initial full recovery remotely verified; immutable10policy/50full; distinct2 local generations
Verified: Python175 + focused23; JS26/build; Chromium DPR/LOD/effects/hover/mobile/500units
Evidence: docs/league-transition/README.md, engine-audit/REPORT.md, legacy-backup.json
Next: monitor200game/confirmation pilot; T07 causal interventions/shared-PPO control and traffic follow-up remain
Limits:500units SwiftShader~11.7FPS under load; actual Mac/strategy improvement/permanent CPU unverified
Environment: league-v1 startup draft saved; user Save/Publish required; usage UNKNOWN
