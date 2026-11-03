# MW-NV v1.0.0 STATE
Current:T28 large capture-flag replay publication fix
Cause:12.5MB PUT HTTP401;identical credentials512KiB PUT+GET succeeds
Changes:verified512KiB chunks+manifest;streaming Pages response;publisher-only runtime override
Tests:Python4/JS61/build PASS;sealed preview PASS;live large-replay recovery pending
Deploy:replay-chunk-stream r1 APPLIED;production marker verification pending
Live:publisher replaced;training/engine/models not restarted;release agent restores publisher override
Read:docs/replay-chunk-stream.md
Next:verify new flag replay in api/matches and stream response;commit final evidence
Limits:40chunks/20MiB compressed;larger rejects and preserves prior pointer
Baseline:A′/B′1189/g2748 preserved;rotation3→4→2 unchanged
Usage:UNKNOWN
