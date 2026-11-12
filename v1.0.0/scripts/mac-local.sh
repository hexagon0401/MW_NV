#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v uv >/dev/null || { echo '먼저 brew install uv 실행'; exit 1; }
command -v ollama >/dev/null || { echo '먼저 brew install ollama 실행 후 별도 터미널에서 ollama serve 실행'; exit 1; }
# Smaller alternative to the blocked Qwen3.5 GGUF candidate; no paid API.
MODEL_NAME="${MW_NV_MODEL:-qwen3:0.6b}"
ollama list >/dev/null || { echo '별도 터미널에서 ollama serve 실행'; exit 1; }
ollama pull "$MODEL_NAME"
mkdir -p data
ollama show "$MODEL_NAME" > data/local-model-info.txt
ollama list > data/local-model-digests.txt
set --
if [[ -n "${MW_NV_POLICY:-}" ]]; then set -- --policy "$MW_NV_POLICY"; fi
uv run --locked --extra server --extra inference python -m server.live --hq local --endpoint http://127.0.0.1:11434/v1 --model "$MODEL_NAME" --port 8000 "$@"
