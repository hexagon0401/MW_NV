# T15 terminal dashboard and authenticated PPO control

Approved: separate /dashboard/ tab, dark terminal UI, <=900ms one-shot decorative
CSS glyph intro (12x20desktop/6x20mobile), public read-only views; GitHub owner
82876856 alone may pause/resume PPO. Evaluation/diagnostics/backups continue.
No arbitrary shell/PID/path commands or new paid services.

Stage1: six public sections, self-hosted Geist Mono1.8.2/OFL, existing NanumSquare;
no Pixi/replay download from dashboard. Spectator retains only current-match
information. Hidden spectator and dashboard suspend rendering/polling.
Validation: JS35passed/build; Chromium1440x900 and390x844 fixture views, lazy
resource charts, reduced motion, once/session intro, zero page errors. Screenshots
in this directory are labeled fixture verification until production rollout.
T11 validation paused before instrumentation; active PPO is preserved.

Next: incremental SQLite telemetry/compact Storage APIs -> OAuth/CSRF + durable
PPO-only command queue -> control gate/safe pause -> regression and deployment.
GitHub provider is not configured; all administrative commands stay disabled
until the OAuth app/provider/session secret and real owner login are verified.
