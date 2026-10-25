# MW-NV v1.0.0 STATE
Current: T05-1 spectator UI/anchored symbols complete
Status: UI tested locally; not deployed yet; next map/art
Changes: anchored22px icons, short IDs, collision suppression/clusters, selection/follow/combat navigation
Chrome: compact training summary + expandable details; map/panel selection; drag/click threshold
Verified: JS21; Vite build; Chromium desktop/mobile/history PASS
Evidence: docs/tactical-redesign/AUDIT.md + ui-overview.png
Training: old self-play-v2 stopped by SIGINT; checkpoint gen225/games83/steps21056 preserved
Migration: actor-only to new rules3 self-play-v3 after combat tests; critic/optimizer reset
Site: existing production https://mw-nv.pages.dev unchanged until integration
Next: implement connected terrain art and new symmetric district map
Blocker: Release uploads.github.com forbidden; local recovery preserved
Hosting: permanent CPU not provisioned; network draft still pending
Limits: Intel Mac unverified; no strategy improvement claim
Usage: UNKNOWN
