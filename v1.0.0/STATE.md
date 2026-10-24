# MW-NV v1.0.0 STATE
Current cycle: C01
Status: PASS
Last completed: C01 minimal bootstrap
Changed: README.md, pyproject.toml, uv.lock, .python-version, config/game.yaml, engine/, tests/test_config.py
Last tests: python -m pytest -q — 10 passed (including width 0/negative rejection)
Additional checks: repeated locked sync, tests without reinstall, installed import from /tmp — PASS
Environment: Linux x86_64, Python 3.12.14, uv 0.12.23
Known blockers: none for C01; actual Intel Mac validation pending
Implemented: config loader only; game, local LLM, viewer and training not yet implemented
Plan checkpoint: 8c4557a (pushed)
Git branch: dev/v1.0.0
Next single task: C02 basic Entity types; read DECISIONS.md + original A/C02 only
Next command: cd v1.0.0 && uv run --locked --extra dev python -m pytest -q
Remaining Plus quota: UNKNOWN
