# Dashboard refresh and manual policy comparison

Polling builds a detached result and commits it only after a successful, current request. Existing content remains visible during network waits/failures. Window scroll, internal scroll, expanded details and focus are restored at commit time. Release logs have stable scroll keys.

Validation: 24 targeted Python tests, 58 JavaScript tests, production build. Chromium desktop 1440×900 and mobile 390×900 delayed-response fixtures preserve content and scroll; release fixtures cover reading older logs without jumping to the end. Images alongside this file show the refreshed activity view. Preview uses the allowlisted t11-multi-mode alias; the unique preview hostname was blocked by the network proxy.

## Manual comparison

READY FOR RELEASE entry `policy-progress-comparison`, revision 4, freezes the 200-game baseline and 769-game snapshot of PPO1/PPO2 under the same legacy rules (`combined-arms-4`, `tactics-2`). Only an authenticated administrator can start it; automatic start is rejected server-side. It has not been started during preparation.

80 cases: two learners × historical/algorithm opponents × five seeds × two teams × two start assignments. The summary reports the 40 historical-opponent cases; algorithm matches provide an additional reference. Victory score is win=1, draw=0.5, loss=0. Seed-level intervals have only five independent seeds; this is a progress check, not proof of general strategy improvement or new-map transfer.

The evaluation never updates weights or invokes NIM. Its ledger, activity, reports and completed replay pointer are isolated from training. One CPU is reserved, the job waits for capacity, completed reports resume on restart, and a global lock prevents simultaneous comparison jobs. The first completed replay opens via the comparison card; only completed matches are published. Upload failures preserve the previous verified pointer. Old comparison replays retain three objects.

Current limitation: no live incomplete-match stream. Replay publication, actual long-run CPU behavior and real-match results are unverified until the user starts the comparison. Existing mixed-map rollback is retained; this feature does not reapply it.
