# MW-NV v1.0.0 STATE
Current task: V03 native pixel art, traffic fixes, paired ten-game recheck
Status: implemented/tested; residual congestion and starting-side bias documented
Art: native pixel/dither, real-vehicle motifs, clustered trees; hover status meters
Engine: distributed drop/parking, wait/yield/replan, FIFO boarding, HEL reservations
Versions: rules combined-arms-2; catalog combined-arms-1; old policy needs retraining
Verified: Python124, JS11, production build, Chromium128+20/hover/mobile/end stats PASS
Soak:10/10 complete; seed0–4 x2; .2s tick; algorithm HQ; 231.5sim min/257.322wall s
Results: failures52.44%→37.43%; transport paths1701→54; embark BLOCKED215→0
Remaining: TRAFFIC_TIMEOUT253; capture/move BLOCKED896; left-side9/10 wins; fuel6
Evidence: docs/pixel-refinement/COMPARISON.md, JSON, ART.md, TRAFFIC.md, screenshots
Next: dispersed capture arrival/infantry replanning and starting-side diagnostics
Recheck: .venv/bin/python -m engine.soak --output /tmp/mw-nv-ten.json
Branch: dev/v1.0.0; no deployment; softwareGPU7FPS; Intel Mac/real LLM unverified
Usage: UNKNOWN
