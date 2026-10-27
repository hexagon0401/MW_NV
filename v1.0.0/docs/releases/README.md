# T23 — READY FOR RELEASE

Public terminal-style release preparation, manual Apply by default, per-content-revision durable automatic intent. Registry stores manifests/state/events/commands/attempt journals in SQLite; public Storage contains only sanitized snapshots and immutable200-row event pages. No browser shell, host paths or secrets. GitHub owner82876856 is the only mutation identity.

Registered: maps2/3/4 mixed package, planned tactics5 and planned map5. Map5 is not implemented. Required gates:30 hash-verified engine games, map2 retention, isolated192-game pilot, fixed/required confirmation evaluation, exact remotely verified recovery and build/geometry checks. No implicit operational transition from validation.

Old21 verified diagnostic cases are retained. In-progress old diagnostic work may restart because the former runner had no mid-case checkpoint. Simulation and journal replay now have separate observer-only progress and heartbeat. Original engine.replay and game rules are unchanged.

Implementation order: registry/read-only UI → validation/pilot isolation → typed apply/rollback → automatic intents → deployed integration. Each milestone tests/STATE/commit/push. Runtime availability is separate from readiness; offline never implies success. Manual and automatic use the same serialized server handler.

Registry content revisions are immutable: changes require a newer revision and clear automatic intent. Administrator set_auto requests are persisted in private Storage authorizations as well as SQLite, independently of cookie expiry. Duplicate IDs preserve acknowledgments even after request expiry. Only the latest per-release intent is republished; old retries cannot re-enable a canceled reservation.

Validation is prepare-only. Candidate pilot uses a frozen source tree, sandbox ledger/status/control/activity, the shared NIM lease, a2-core reservation and one simulation worker. Initial evaluation is serial. Completed pilot exits at its safe update boundary and archives the exact final generation. No candidate ledger is imported on operational adoption; operational_start_games distinguishes inherited learning from new operational games.

Apply worker is serialized with flock plus durable phase journal. Mixed adapter snapshots/stops the registered operational runner at a safe boundary, remotely verifies recovery, restores the verified candidate into a new owned root, preserves current administrator pause, then verifies the actual coordinator registration. Rollback restores a frozen compatible runtime; no model/RNG/optimizer is mixed across rules. Pages adapter validates manifest hashes, uses fixed wrangler argv, verifies the public marker and deployment ID, and supports the prior Cloudflare deployment. These adapters are tested with isolated fake effects; the real mixed package cannot be applied before its long readiness gates finish.

Developer Pages registration: `.venv/bin/python -m server.release_stage pages --id <id> --revision <n> --source <built-viewer> --title <title>` creates a VALIDATING candidate, not approval. Use `certify --id <id> --report <proof.json>` with actual test/build/preview/rollback results identifying the exact artifact checksum. Browser API cannot register paths or fabricate proofs. New validation adapters are code-reviewed additions, not manifest-supplied code.
