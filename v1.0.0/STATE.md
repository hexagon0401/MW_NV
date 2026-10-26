# MW-NV v1.0.0 STATE
Current: T11 stages1-4 engine/missions complete; stage5 policy implemented; stages6-7 in progress
Contract: docs/multi-mode/PLAN.md; same independent PPO1/PPO2 across conquest/elimination/CTF
Verified: stage5 targeted13 pass; NumPy logits max error3.4e-7; permutation/critic isolation/save-load
Migration: each old actor separately distilled on64 TRAIN rounds (7034/7080 matched candidates)
Migration limits: KL0.827→0.733 and1.061→0.859; retention evaluation pending, no promotion
Geometry:30seeds each new map passed; docs/multi-mode/geometry.json
Live: old league-v1 retained,29completed at last read; no mixed training or T11 deployment
Versions: opt-in new worlds rules5/catalog3/tactics3; legacy default rules4/catalog2/tactics2 retained
Next: mixed runner/state/evaluation,mission stats/viewer;30-game audit and frozen migration gate
Remaining:192mixed pilot,mode-specific evaluation,actual Pages preview/production QA
Site: https://mw-nv.pages.dev productionbdd8e560; existing model/replay/statistics preserved
Real Intel Mac/permanent CPU unverified; no strategic improvement/transfer claim
Usage: UNKNOWN
