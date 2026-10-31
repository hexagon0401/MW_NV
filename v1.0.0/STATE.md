# MW-NV v1.0.0 STATE
Current:T26 register 10-completed-game map rotation update
Changes:config/releases.yaml;docs/map-rotation-10.md;DECISIONS.md
Behavior:planned 2→3→4 rotation;10 unique completed training games each;same PPO1/PPO2
Validation:manifest schema,PLANNED/manual/no attempts/dependency gate checked in temp registry
Registry:map-rotation-10 r1 registered;auto=false;no training change/no Apply issued
Blocker:mixed-maps remains ROLLED_BACK;rotation implementation and recovery checks pending
Deploy:data-only release catalog update;existing dashboard-admin-session deployment retained
Read:docs/map-rotation-10.md
Next:restore mixed-map runner;implement schedule/parallel quota/resume/balance;new revision→READY
Comparison:separate policy-progress-comparison retained;no comparison command issued in T26
Usage:UNKNOWN
