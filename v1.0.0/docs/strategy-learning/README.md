# T22 — strategy learning reliability and exploration

Goal: independent PPO1/PPO2 learn all modes2/3/4; victory first, then losses/resources, then time. Map5 is deferred (future side lengths3–5× map2). No universal optimum or transfer claim.

Order: correctness →30 diagnostic games/retention→192-game mixed pilot→gated tactics-5 routes/opponent diversity→three-arm NIM comparison→heldout tactic/transfer evidence. Keep old actors/optimizers/replays and remote verified recoveries. Do not promote untested actors.

## Stage1
The real update now calls TeacherBuffer.imitate/sample_rows (mission quotas13/13/6). Training, teacher and evaluation share decision_inputs.encode; tactics-4 keeps its original prefix-feature history; a deeper audit corrected the initial mistaken assumption that history was empty. Metadata mission-inputs-2 identifies corrected samples. Old samples remain in original archives but are excluded on load, not silently guessed. Legacy tactics-2 inputs are unchanged.

MaskablePPO target_kl=.02 uses installed SB3-Contrib. Auxiliary imitation measures masked forward KL and clips gradients(.5); KL>.02/nonfinite restores only the post-PPO auxiliary starting weights+optimizer. Actual sample mode/stage/team counts and SB3 train diagnostics are persisted in update metadata.

## Research reuse and expected effects
Exact upstream commits/file hashes/licenses and installed package versions are in sources.json. No source files were copied. Existing pinned SB3/SB3-Contrib are reused; no MuJoCo/TensorFlow/OpenSpiel framework installation.
- OpenAI emergence environments(MIT): module/wrapper separation, visibility masks and randomized training environments. Expected less fixed-layout memorization; emergence is not guaranteed.
- SB3-Contrib(MIT): existing masked PPO and KL guard. Expected fewer illegal choices and excessive policy changes.
- CleanRL(MIT): independent PPO diagnostics reference. Expected actionable collapse/value/entropy diagnostics, not automatic strategic gain.
- OpenSpiel(Apache-2.0): policy population/payoff ideas; implement lightweight selection, not a full PSRO/Nash solver. Expected reduced narrow-opponent overfit.
- OpenAI Baselines/SB3(MIT): online mean/variance combination; use installed RunningMeanStd for telemetry only. Never normalize masks/flags or mutate heldout statistics.

Each stage: meaningful tests → STATE≤15lines → commit → push. Engine diagnostics may only carry forward with byte-identical dependencies; affected policy evaluations must rerun. This report does not assert a completed192-game pilot or NIM efficacy.
