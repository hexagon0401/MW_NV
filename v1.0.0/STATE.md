# MW-NV v1.0.0 STATE
Current:T26r2 WIP rotation3→4→2 and latest capture-policy preservation
Changes:mission_schedule rotation_descriptor;serial collector;RotationTraining typed handler
Tests:rotation boundaries/resume/480game balance2 PASS;release21 PASS;integration running
Runtime:legacy STOP release:map-rotation-10:2 requested at safe boundary;archive task active
Baseline:waiting data/rotation-baseline.json;must preserve latest A′/B′ on GitHub before mixed Apply
Source:DO NOT use old mixed63-generation policy;user requires latest capture-policy distillation
Smoke:/tmp/mw-rotation-smoke.log; /tmp/mw-rotation-regression.log
Next:verify baseline archive→distill each tactics2→4→prepare verified candidate→READY→Apply
Pending:no release rotation READY or Apply yet;config r2 not live registered
Safety:legacy stopped intentionally for baseline;resume if migration/archiving cannot finish
Usage:UNKNOWN
