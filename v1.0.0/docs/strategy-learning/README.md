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

## Implemented successor tools (gated, not deployed learning results)
`tactics-5` uses2112 inputs and65 actions, a shared32-feature row encoder, NumPy parity, true10/20-second summaries with checkpoint recovery. Public-observation weighted routes are bounded to4 goals×3 styles×20,000 expansions; their length/risk/cover are estimates. Unknown explored coverage is−1, never inferred from absence of enemies. Engine still verifies physical movement. Group quotas16 each redistribute unused capacity.

Training-only variants change resources by±20%, thin existing forest and attempt legal32m spawn shifts with explicit0-offset fallback; default release maps stay unchanged.64m is an explicit future curriculum setting, not automatically enabled.

Population registry retains up to32 time/style representatives with remote checksum references. Local cache8 preserves pinned policies and never deletes an unverified sole copy. Selection-only seeds9000–9999 are separate from final evaluation; final scores cannot enter payoff updates. A population probe evaluates one least-measured opponent per learner,8 crossed games each, only at successor evaluation boundaries.

`learning.exploration_bootstrap --pilot data/mission-normalization-v2 --root data/strategy-v1` requires completed192-game nonregressing tactics4 pilot and exact remotely verified frozen source recovery, then command-matched distillation and separate map2 retention. It does not replace production actors. Successor run requires its certificate and `MW_NV_EXPLORATION=1`; ordinary teacher only (`MW_NV_DISABLE_MISSION_COACH=1`) until2112-input demonstration history parity is separately implemented/tested. This limitation is enforced, not silently converted into1600-input labels.

NIM comparison now has3 conditions×3 seeds(8021–8023),128updates each, serial1-worker trials, isolated control/ledger/status and shared request broker. Completed trial/source hashes are immutable. CPU/wall totals cover completed invocations; interrupted overhead is not claimed as fully accounted. The dependent study waits for completed mixed pilot, not only engine diagnostics.

New APIs preserve existing fields. Generation/execution/evidence filters currently drill into bounded recent examples, explicitly labelled `recent_examples_only`; lifetime aggregates keep their original mode/scenario scope. Full historical generation aggregation is not yet implemented. The evidence classifier requires explicit heldout/cross-side replication and ablation before higher labels; a match alone remains insufficient.

## Acceptance and limits
Python full regression286 passed405.77s at the stage2 snapshot, followed by scoped tests for later changes; JS49 passed/build and desktop/mobile Chromium fixture tests passed on local and Pages preview assets. Later scoped results and deployment/runtime checks are in validation.json. Fixtures do not prove real NIM efficacy or192-game pilot completion.

Remaining measured work: finish30-game diagnostics and retention; run192-game mixed pilot; run3-arm teacher study; successor retention/route performance; heldout tactic/transfer evaluations. No strategy improvement or large-map performance claim. Engine diagnostics21 cases carry forward only with52 unchanged engine/agent/config dependencies plus matching pre/post20-second command journals/state hashes in all3 modes (diagnostic-continuity.json). Policy evaluation is not carried forward.
