# MW-NV v1.0.0 STATE
Current task: CA05 combined-arms art and final integration
Status: PASS functional; Mac hardware/model validation pending
Completed: CA01 catalog/64+10, CA02 combat, CA03 hybrid/PPO, CA04 ledger, CA05 art
Verified: Python 118 PASS; JS 11 PASS; production build PASS
Browser: desktop/mobile, 128+20 scene, live casualty/reconnect and ended-game stats PASS
Learning: 2x64-step train/parity; continuous frozen-opponent resume PASS
Evaluation: held-out seed10000, policy alternates A/B, 0W/2L; no promotion
Performance: SwiftShader software GPU only; see docs/combined-arms/verification.json
Compatibility: versioned engine replay; old display replays supported
Run Mac: bash scripts/mac-local.sh; viewer npm run dev; see COMBINED_ARMS.md
Next: actual Intel Mac/model validation and larger held-out balance study
Branch: dev/v1.0.0; deployment deferred
Usage: UNKNOWN
