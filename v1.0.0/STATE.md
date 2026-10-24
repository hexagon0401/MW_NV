# MW-NV v1.0.0 STATE
Current task: G01 gameplay, transport, local LLM launch and repeat training
Status: functional checks PASS; Mac/model inference unverified
Completed: ranged engagement/retreat, carrier detours, 28-person release teams
Viewer: HP/shot lines/targets, directional soldiers, darker district map/effect labels
Verified: Python 92 PASS; JS 9 PASS; production build PASS
Browser: desktop/mobile/fonts/tooltips and live casualty/reconnect PASS
Transport: release run observed embark/disembark; follow-up landing/HQ fixes tested separately
Learning: three 64-step PPO rounds, frozen-opponent resume/save/NumPy parity PASS
Run Mac: bash scripts/mac-local.sh; viewer npm run dev; see GAMEPLAY_UPDATE.md
Run repeat: python -m engine.series --count 0
Run CPU learning: python -m learning.continuous --rounds 0
Next: Mac model validation and balance/held-out evaluation; deployment deferred
Git branch: dev/v1.0.0
Usage: UNKNOWN
