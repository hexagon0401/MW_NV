# MW-NV v1.0.0 STATE
Current phase: release verification
Status: PARTIAL_EXTERNAL (local software verified; external release pending)
Verified: C01-C27 core/replay/viewer/API; C31-C35 CPU learning/evaluation
Last tests: 83 Python passed; 6 JS passed; production build passed
Browser: Chromium dev and production API paths PASS
Private gate: actual Pages runtime anonymous HTML/replay/API all 401
Evaluation: 50 Random + 50 Rules; 320 holdout matches; rules retained
Model runtime: llama.cpp 3032209 CPU build/version PASS; GGUF not downloaded
Storage: user chose Supabase private; R2 remains disabled
External requirements: SETUP_ACTIONS.md and RELEASE_STATUS.md
Git branch: dev/v1.0.0
Next: secure keys + Access settings + model network, then external verification
Fresh GitHub clone: 83 Python + 6 JS/build PASS; minimal without Torch 80 PASS / 2 optional SKIP
Remaining Plus quota: UNKNOWN
