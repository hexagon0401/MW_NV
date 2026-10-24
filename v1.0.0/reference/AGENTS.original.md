# DECEPTION CTRL v1.0.0 — Codex Rules

This directory is a **version-isolated project**. Do not modify sibling version directories or unrelated user files. Preserve all existing changes.

## Read minimally

1. Start with `STATE.md` (if absent, next cycle is `C01`).
2. Read only section `A` of `CODEX_EXECUTION_PLAN.md` and the single relevant `Cxx` task card; **never load the full long plan** unless the user explicitly asks for a full review.
3. Use `rg -n '^#### C[0-9][0-9]\.' CODEX_EXECUTION_PLAN.md` to find the requested card and read only its nearby lines. Read other specification sections only when the task requires their exact settings.

## One focused cycle

- Implement **one Cxx task** per invocation; if incomplete, keep the same Cxx for next time.
- Prefer max 3 implementation files changed (excluding tightly coupled tests/config). Avoid unrelated refactoring and premature dependencies.
- Run directly relevant tests and document actual output. Never claim unrun tests passed.
- Stop and report when the task succeeds, a blocker requires user input, or the usage budget is near exhaustion.
- Plus usage target: stop at or before **90% of the visible available quota**, retain **10% reserve**. No fixed quota or usage percentage may be invented; check `/status` or ChatGPT Usage if accessible.
- Target cadence: **at most 3 manually authorized cycles/day** (suggested KST 08:00, 14:00, 20:00); no automatic background execution is implied.

## Architecture contract

- A/B HQ AI **only reads observations and emits validated game opcodes**.
- The deterministic engine alone handles movement, collisions, detection, abstract combat, capture, transport, logistics, and scoring.
- **No LLM calls per soldier/vehicle or per physics tick.** Core game must work with rule-based HQ and no LLM.
- All v1.0.0 vehicles are **non-weaponized transports**. They move, load/unload, and consume fuel; they do not attack.
- Use the exact invented pixel sizes, speeds, vision distances, roles, and collision footprints from `CODEX_EXECUTION_PLAN.md` sections D–G.
- No live network exploitation or arbitrary OS/shell command execution by game agents. They may issue only the game's allowlisted action schema.

## Reporting

After each cycle, keep `STATE.md` short: Cxx ID, PASS/PARTIAL/BLOCKED/BUDGET_STOP, changed paths, tests, blocker, next ID, quota UNKNOWN or measured. Report the same concise facts to the user.
