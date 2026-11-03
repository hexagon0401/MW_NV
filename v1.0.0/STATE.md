# MW-NV v1.0.0 STATE
Current:T28 large capture-flag replay publication fix
Cause:12.5MB PUT HTTP401;identical credentials512KiB PUT+GET succeeds
Changes:verified512KiB chunks+manifest;streaming Pages response;publisher-only runtime override
Tests:Python replay/release PASS;JS61/build PASS;sealed preview PASS;live API complete decode PASS
Deploy:replay-chunk-stream r1 APPLIED;production1bc3b916 marker verified
Live:publisher replaced;training/engine/models not restarted;release agent restores publisher override
Read:docs/replay-chunk-stream.md
Verified:api/matches latest capture_flag;HTTP200/full JSON ended=true/duration3600s;3 replays retained
Limits:40chunks/20MiB compressed;larger rejects and preserves prior pointer
Baseline:A′/B′1189/g2748 preserved;rotation3→4→2 unchanged
Usage:UNKNOWN
