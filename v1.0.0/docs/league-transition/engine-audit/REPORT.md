# rules4 engine audit

Ten headless algorithm games; not PPO/NIM training or evidence of improvement.

| seed | swap | score A:B | winner |
|---|---|---|---|
| 20000 | False | 102:49 | A |
| 20000 | True | 73:100 | B |
| 20001 | False | 100:93 | A |
| 20001 | True | 11:102 | B |
| 20002 | False | 30:101 | B |
| 20002 | True | 7:101 | B |
| 20003 | False | 16:103 | B |
| 20003 | True | 41:102 | B |
| 20004 | False | 101:15 | A |
| 20004 | True | 101:24 | A |

A4/B6; west7/east3. Deterministic recorded-action reexecution: True. Total runtime 947.4s.

Failures: {"ILLEGAL_STATE": 101, "EXPIRED": 82, "TRAFFIC_TIMEOUT": 330, "FORMATION_UNREACHABLE": 17, "INSUFFICIENT_SUPPLY": 16, "INVALID_TARGET": 4, "UNOBSERVED_TARGET": 25, "NO_FUEL": 8}
Formation events: {"FORMATION_REPLAN": 404, "FORMATION_COLUMN": 457, "FORMATION_ARRIVED": 297}
Friendly damage total 8. Long-stationary observations 45 (includes boarding waits; not all are stuck movement).

The mirrored narrow-bridge fixtures prove the targeted formation regression is fixed. These ten full games still contain traffic/formational failures and a starting-side skew; no claim all movement issues or balance are solved. Compared with the previous west8/east2 audit, the side skew remains; the candidate/schedule conditions must be matched before attributing a cause.

This audit process loaded the pre-expansion tactical generator before tactics-2 edits. It tests rules4 movement with that generator; it is not the 10-second dual-PPO pilot.
