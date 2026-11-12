# MW-NV

[한국어](README.md) | English

MW-NV is an experimental project combining a deterministic battlefield simulation, AI command, reinforcement learning, and pixel-art spectating. Two teams manage infantry, vehicles, transport, and supplies. The engine handles movement and combat while AI selects command candidates using permitted observations.

[Spectator site](https://mw-nv.pages.dev/) · [Operations dashboard](https://mw-nv.pages.dev/dashboard/) · [Current work state](v1.0.0/STATE.md) · [Design decisions](v1.0.0/DECISIONS.md)

> This project is under development. Historical experiment reports may not reflect the current deployment. Check the dashboard's last update and execution status to see whether training is running.

## Features

- **Deterministic engine:** A fixed 0.2-second tick and seed drive movement, visibility, combat, capture, transport, and supply.
- **Combined arms:** Infantry squads, transports, armored vehicles, tanks, artillery, helicopters, and anti-air equipment have roles and game-balanced characteristics.
- **Three game modes:** Map 2 is control-point capture, map 3 is elimination, and map 4 is capture the flag. The mixed-training schedule is configured to rotate through elimination, capture the flag, and control-point capture in batches of 10 completed training games.
- **Spectating:** Replay completed matches, browse the three most recent replays, and inspect team status, orders, combat effects, and match history. A separate server supports local live spectating.
- **Training and evaluation:** Independent PPO1 and PPO2 policies play against each other, historical policies, and rule-based opponents. Training matches and fixed-policy evaluations are recorded separately; checkpoints support policy preservation and recovery.
- **AI command:** Each team receives a separate observation. Rule-based HQ and local LLM or NVIDIA NIM connections are supported, and the engine validates commands. Available connections and fallback behavior depend on the selected execution mode and configuration.

## Quick start

### Requirements

- Git, Python **3.12**, and [uv](https://docs.astral.sh/uv/)
- Node.js **22.12 or newer, or 24**, and npm for the viewer
- A Linux CPU environment for PPO training. Intel Mac is a primary target for local viewing and NumPy policy inference; actual Mac performance requires separate verification.

```bash
git clone --branch dev/v1.0.0 https://github.com/hexagon0401/MW_NV.git
cd MW_NV/v1.0.0
uv sync --locked --extra dev --extra server --extra inference
uv run --locked --extra dev pytest -q
uv run --locked python -m engine.headless --seeds 1 --release
```

`dev/v1.0.0` is the development branch. Check GitHub for the repository's actual default branch and deployed version. Project code lives under `v1.0.0/`.

### Watch a local replay

In the first terminal:

```bash
cd MW_NV/v1.0.0
uv sync --locked --extra server --extra inference
uv run --locked python -m engine.viewer_export
mkdir -p data
cp viewer/public/demo.json data/demo.view.json
uv run --locked --extra server python -m uvicorn server.app:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd MW_NV/v1.0.0/viewer
npm ci
npm run dev
```

Open the local address printed by Vite. Stop each process with `Ctrl+C` in its terminal. See the [server guide](v1.0.0/server/README.md) for local live matches and SSE spectating.

### Checks

```bash
cd MW_NV/v1.0.0
uv run --locked --extra dev pytest -q
npm --prefix viewer ci
npm --prefix viewer test
npm --prefix viewer run build
```

For learning-related checks on Linux, install the optional dependencies with `uv sync --locked --extra dev --extra server --extra learning`. Distinguish skipped optional checks from a full passing suite.

## Game modes

| Mode | Objective |
| --- | --- |
| Control points | Secure objectives and earn points. |
| Elimination | Exhaust the opponent's combat tickets or ability to recover combat power. At the time limit, remaining tickets are compared relative to each team's initial tickets. Purchase credits and combat tickets are separate resources. |
| Capture the flag | Use infantry to secure the enemy flag and return it to your base. Capture scores and time-limit rules also apply. |

The engine and scenario configuration determine the actual outcome. Re-executing a replay under a different rules version requires a compatibility check. See [combined arms](v1.0.0/COMBINED_ARMS.md) and [multi-mode documentation](v1.0.0/docs/multi-mode/README.md) for details.

## Training and operations

```text
Team-specific observations → tactical candidates → PPO policy → engine validation and execution
                                    ↘ NIM teacher samples are used for separate imitation learning
Completed matches and checkpoints → private storage/archive → spectator site and dashboard
```

The current design keeps PPO1 and PPO2 independent. NIM teacher responses are stored separately for imitation learning rather than treated as PPO's own on-policy actions. Progress is assessed against fixed historical policies and held-out seeds and sides. More matches or a higher raw win rate alone do not establish strategic improvement or generalization to a new map.

The capture-focused baseline was preserved before mixed training at 1,189 games and generation 2748. See the [baseline record](v1.0.0/docs/capture-baseline-1189.md) and [GitHub Release](https://github.com/hexagon0401/MW_NV/releases/tag/capture-specialists-1189-g2748). Migration to the mixed policy's different input contract distills each actor separately and starts a new critic and optimizer.

Cloudflare Pages serves the viewer and API; it does not run PPO. Games and training run in a separate CPU environment, and completed results are published to private Supabase Storage. A background process in a Codex environment can continue after a conversation ends while that environment remains alive, but **continuous operation after the environment stops is not guaranteed**. External Workers-based monitoring is currently deferred.

## Repository layout

| Path | Contents |
| --- | --- |
| `v1.0.0/engine/` | Game state and rules, movement and combat, replays, and viewer data |
| `v1.0.0/agents/` | Team-observation-based command candidates and HQ logic |
| `v1.0.0/learning/` | PPO, self-play, evaluation, records, and checkpoints |
| `v1.0.0/viewer/` | PixiJS viewer, dashboard, and Pages functions |
| `v1.0.0/server/` | Local API, live spectating, and operational controls |
| `v1.0.0/cloud/` | Cloud storage and integration code |
| `v1.0.0/config/` | Scenarios, catalogs, and release specifications |
| `v1.0.0/docs/` | Design, validation, and operational records |

## Further documentation and resuming work

- [Detailed project guide](v1.0.0/README.md) · [Combined arms](v1.0.0/COMBINED_ARMS.md) · [Multi-mode](v1.0.0/docs/multi-mode/README.md)
- [Dashboard](v1.0.0/docs/dashboard/README.md) · [Release preparation and application](v1.0.0/docs/releases/README.md)
- [Adaptive execution and recovery](v1.0.0/docs/adaptive-acceleration/README.md) · [Long-running operation design](v1.0.0/docs/runtime-continuity.md)
- [Third-party dependencies and licenses](v1.0.0/THIRD_PARTY.md)

Some detailed documents preserve the state at the time they were written and may contain older execution examples or pre-deployment descriptions. When resuming work, first read the latest entries in `v1.0.0/STATE.md` and `DECISIONS.md`.

Do not commit model files, virtual environments, API keys, or large execution logs. Store external-service secrets in secure environment settings, not in chat or public documentation.

## License

Project code is licensed under the [MIT License](LICENSE). Third-party libraries, fonts, and models have their own licenses.
