# Gameplay update checks

Chromium: existing replay fixture, new directional soldier sprites, darker ground,
HP bars, tooltip values, desktop/mobile controls; live casualty/reconnect smoke PASS.
The replay fixture predates the expanded roster (its 16/team is intentional).
Actual new release scenario is 28/team, covered in Python tests.
Linux CPU: PPO round 0 and resumed frozen-opponent round 1 (64 steps each)
completed; train() checks saved-model and NumPy inference parity.
One repeat-series match completed at tick 6000, 197 attacks, zero rejected commands.
These tiny training checks establish execution, not improved strategy.
Mac/Ollama model inference and game balance remain unverified.
Release 900s scripted RuleHQ run observed 128 embark, 96 disembark and 284 attacks.
It also revealed repeated transport replacement/landing failures; subsequent fixes
keep running vehicle orders and use cleared objective approaches for landing.
