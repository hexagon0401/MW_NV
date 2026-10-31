# MW-NV v1.0.0 STATE
Current:T25b administrator session synchronization hotfix
Changes:await session before render;refresh auth on focus/poll;truthful footer;fail closed on error
Tests:58 JS/build;Chromium desktop/mobile delayed auth,expiry,cross-tab,failure,retry PASS
Regression:dashboard delayed-response scroll/content preservation PASS
Preview:sealed dashboard-admin-session r1 passed session fixtures;no execution POST sent
Deploy:dashboard-admin-session r1 APPLIED;canonical0bfbc016 and marker verified
Comparison:policy-progress-comparison r4 READY/manual;200 vs769 snapshots;NOT STARTED by assistant
Runtime:legacy PPO preserved;mixed-maps remains ROLLED_BACK
Read:docs/dashboard-refresh/README.md
Next:user opens comparison card;authenticate then manually start if desired
Limits:user browser cookies cannot be inspected;real GitHub login requires user browser
Usage:UNKNOWN
