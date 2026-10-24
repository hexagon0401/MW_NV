# MW-NV v1.0.0 STATE
Current task: D03 design and local live integration
Status: PASS (functional); deployment deferred by user
Completed: D01 Swiss UI/fonts, D02 pixel battlefield, D03 local snapshot/SSE
Changed: viewer/, engine/viewer_export.py, server/live.py, server/app.py, tests/, docs/design/
Verified: 89 Python tests, 9 JS tests, production build PASS
Browser: desktop/mobile/fonts/hover/tap/real casualties/server restart reconnect PASS
Physics: observed and unobserved RuleHQ game checksums match
Performance: 500 infantry, SwiftShader 13–17 FPS; Intel Mac GPU unverified
Visual evidence: docs/design/desktop.png, mobile.png, live.png, verification.json
Run: python -m server.live --hq rules --port 8000; viewer npm run dev → 진행 경기
Git branch: dev/v1.0.0
Next: user review; external release requirements remain in RELEASE_STATUS.md
Remaining Plus quota: UNKNOWN
