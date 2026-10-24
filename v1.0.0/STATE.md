# MW-NV v1.0.0 STATE
Current task: V02 natural-light 2D refresh and ten-game soak analysis
Status: art PASS; 10/10 games completed; systemic movement issues found
Art: 4x unit / 3x facility / 2x ground atlases, cel shading/dither/contact shadows
Verified: 11 JS tests, production build, Chromium 128+20/hover/mobile PASS
Soak: seed0–4 x2 sides, algorithm HQ, unchanged .2s tick, no sleep
Results: A5/B5, 290 simulated minutes / 310.809 wall seconds (~56x)
Issues: 1701 vehicle path failures; 577 blocked; 52.4% accepted orders fail
Invariants checked: 0 violations; no claim that all system errors are absent
Evidence: docs/visual-refresh/REPORT.md, JSON, screenshots and DESIGN.md
Next: parking/drop slots, traffic replanning, squad boarding queues; rerun same seeds
Branch: dev/v1.0.0; no deployment; Mac/real LLM unverified
Usage: UNKNOWN
