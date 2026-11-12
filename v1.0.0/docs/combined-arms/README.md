# Combined-arms verification

Verified on Linux cloud CPU / Chromium SwiftShader, not Intel Mac hardware.

- Python: full 118 tests PASS, plus optional-dependency-guard regression checks.
- JavaScript: 11 tests PASS; Vite production build PASS.
- Catalog: 64 infantry / 10 vehicles per team; unique IDs, resources and caps.
- Combat: armor/air multipliers, LOS, ammunition, min/max artillery range,
  deployment/pack, observed/expired coordinates, seeded scatter and friendly damage.
- Transport: casualties permit survivor boarding, destroyed carriers evacuate,
  expired orders release vehicles and individual orders replace squad movement.
- Navigation: MBT routes connect both spawns to every objective; map is symmetric.
- Determinism: recording replay and detached spectator frames preserve state hashes.
- HQ: hidden enemy movement does not change candidates, candidate IDs are bounded,
  duplicate/conflicting/invalid LLM choices fall back, supply/credits/tickets reserve.
- Ledger: win/loss/draw, mode/rules/policy separation, interrupted games excluded,
  atomic duplicate-safe imports and frozen-checkpoint/training-run step mapping.
- Browser: live 64+64 infantry / 10+10 vehicles, HP tooltips, terrain, mobile panel,
  real casualty/SSE restart checks, and end-of-match frozen-screen W/L/D refresh.

`combined-forces.png` uses synthetic packed display positions to inspect all 128
infantry and 20 vehicles. It is a rendering fixture, not a simulated battle outcome.
`armor-detail.png` and `district-overview.png` use the actual release live runner.
`stats-and-hq.png` displays imported real evaluation results. `mobile.png` checks layout.
`verification.json` contains measured FPS/JS timing and actual GL renderer.
Software-GPU FPS is not a Mac performance claim or a 30 FPS acceptance result.

Two 64-step candidate PPO rounds passed CPU save/load and NumPy action parity.
The new continuous runner was also started and resumed for two 64-step rounds,
with the second playing the frozen first policy; checkpoints publish atomically.

`evaluation.json`: held-out seed10000, learned policy alternates A/B against rules.
The small policy lost both matches (0W/2L), so it is not promoted. A/B team totals
are 1W/1L each; policy W/L stays distinct from which team the policy controlled.
Only two evaluation matches were run; this is a pipeline check, not a quality study.
Weights, runtime SQLite databases and large logs are deliberately not committed.

Actual Mac inference speed, Ollama model behavior and GPU performance remain
unverified. Deployment remains deferred. See ../../COMBINED_ARMS.md for commands.
