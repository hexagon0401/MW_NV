# T09 implementation evidence

Viewer: wheel/pinch zoom at cursor, drag pan; real units at20%, icons below18% with hysteresis. Text uses screen coordinates, font readiness and DPR<=2. Pixel sprites retain nearest filtering. Tank visual travel180ms/trail300ms; artillery follows recorded timing with tangent/trail; offscreen source arrows are cosmetic. Engine damage timing is unchanged by viewer.

`browser.json` and screenshots: synthetic 128 infantry/20 vehicle scene, DPR1/2 and zoom6/18/19/20/35/65; desktop1440x900, tablet1024x768, mobile390x844. Actual Mac input is unverified. JS25/build pass. Training stopped safely at2090 and preserved before engine changes. Latest actual replay seed39 had BLOCKED91/TRAFFIC_TIMEOUT10; this is one game, not the user's identified match.

GitHub Release upload actually returned HTTP401. Code push and API read authentication do not establish asset upload authentication. Pending models must not be deleted.

Viewer deployment: https://233d76e4.mw-nv.pages.dev (production branch). Movement unit checks: footprint-aware A*, narrow4m bridge mirrored8-member crossings, bounded unreachable target, existing formation speeds/path/replay/transport. Full ten-game audit in progress. Old actual replay B06 failed capture commands at ticks573/759/1059; its final formation was fragmented. Exact screenshot match is not established.

## Dual learner execution

`learning.league` is a single locked CPU coordinator. PPO1/PPO2 have independent actors, critics, optimizers, generators, rollout and teacher buffers. Their initial actors are copied from the pinned rules3 checkpoint; critics/optimizers/counters/buffers are fresh. New rules `combined-arms-4`, contract `tactics-2`; dimensions1056/65 and actor128x128 remain. Raw own-team observations are cached only within an engine decision barrier to avoid repeated full terrain copies.

Tactics every10sim seconds, paired anonymous NIM every30seconds, never per physical tick. NIM actual smoke: two requests/one paired response/eight labels in0.6s; token usage UNKNOWN. The engine pauses during queries. A failed half-pair discards both labels; HTTP429 cooldown persists. Teacher labels train only the assigned learner, with separate32-sample actor imitation, weight0.05/clip0.5/buffer10000.

Actors remain frozen for64 tactical rounds; only real selected actions enter their own rollouts. Rewards are the existing zero-sum score/disabled-value/win rewards accumulated over10seconds. GAE gamma=0.99^(1/3), lambda=0.95^(1/3) at simulation advance; both equal1 between selections within one HQ round. No fake STOP experience for finished teams. Terminal boundaries prevent reward propagation into the next match.

A seeded32-match block has16 duels,8 historic opponents,8 algorithm opponents, crossed learner/team/location. Historic sampling is50% immutable initial /50% recent pool (8 snapshots per learner, active opponent retained). All four map families cross each role combination across four blocks. Candidate generation adds flank/cover and transport-destination choices, suppresses identical active orders and timed failed goals, and allocates slots across roles/actors. No individual aiming learned. Discovery remains bounded by supplied game actions.

## Evaluation and acceptance

Before training and every50 completed training matches: each frozen learner vs initial policy and algorithm,5 held-out seeds x2teams x2starting locations. Identical initial actors/cases reuse results, without inventing extra matches. Exact frozen actors and incremental reports remain in `evaluations/`; interrupted evaluation resumes by case ID. No NIM/teacher/PPO updates in evaluation.

At200 matches: paired seed-cluster bootstrap95% intervals versus initial results. If an interval is entirely below-0.10, pause. Otherwise continue if safety checks pass. An observed positive candidate triggers confirmation on20 additional held-out seeds x4roles. Confirmation reports policy performance within tested scope, not tactical causality or new-map transfer. A shared-PPO equal-budget control has not been run.

Statistics preserve run/learner/team/location/opponent, policy-generation spans, role+tactic opportunities/selections, order acceptance/completion/failure and early/mid/late counts. Sequence detectors track unload-to-same-squad capture, artillery-to-capture, defend-to-hold and repaired-vehicle survival/operation over60s. Capture events explicitly record participants. Missing/censored evidence is separate. `/api/insights` and the PPO dialog expose observational fingerprints and match history; causal intervention claims are not generated.

## Recovery and archival

Old rules3 generation2090: `legacy-backup.json` proves remote chunk download/SHA256, actor+optimizer load and world decode; execution requires its recorded matching code commit. The small index is stored on `training/checkpoints`.

New runs: immutable policies/statistics every10completed matches and full recovery every50 at consumed update boundaries. Initial full recovery is also spooled. Each512KiB transport chunk and reconstructed archive is checked, then models/NumPy and isolated world stepping are checked before metadata index and local cleanup. Monthly Release parts cap250assets; old remote assets are never deleted. Upload failures preserve local spool;2GiB pending or1GiB free reserve pauses safely. Local consumed checkpoints retain2 generations and opponents8/learner, with baseline pinned. Evaluated actors remain pinned; no auto promotion.

Download a transport manifest from its indexed release, then:
```
.venv/bin/python -m learning.league_archive download --manifest <manifest.json> --tag <release-tag> --output data/download
.venv/bin/python -m learning.league_archive restore --archive <archive.tar.gz> --sha256 <sha256> --root data/league-restored
.venv/bin/python -m learning.league --root data/league-restored --source <initial-actor.npz>
```
The restore destination must be empty. Checkpoint restores both optimizers, engine/decision/history state, RNGs, teacher samples/cooldown and schedule; ledger merges check conflicts and are idempotent. A PID and flock prevent duplicate CLI workers. STOP/SIGTERM/SIGINT are consumed at the next completed collection/update boundary; frozen evaluations checkpoint after each case and may delay stopping until evaluation finishes.

The200-match pilot is long-running work, not a synchronous test; its live phase and progress must be reported honestly. No claim of completed200 matches, stronger tactics, permanent hosting, or actual Intel Mac performance before verification. Pages remains viewer/API; Linux CPU performs training.
