# 로컬 게임 개선 / 실행

## Mac 로컬 LLM

저장소에서 `git pull --ff-only` 후 `cd v1.0.0`.
처음 한 번 `brew install uv ollama`, 별도 터미널에서 `ollama serve`.
게임 터미널에서 `bash scripts/mac-local.sh` 실행.
관전 터미널에서 `cd viewer && npm ci && npm run dev`,
브라우저 `http://127.0.0.1:5173/?mode=live` 접속.
LLM 오류/60초 초과 시 규칙 HQ로 복구하며 로그에 기록한다.

기존 Qwen3.5 GGUF 후보는 배포 사이트 접근 오류로 미검증이다.
이 스크립트는 대안 Qwen3 0.6B(Ollama `qwen3:0.6b`, Apache-2.0 계열)를 사용한다.
실제 내려받은 정보와 digest는 `data/local-model-*`에 기록한다.
모델 원본: https://huggingface.co/Qwen/Qwen3-0.6B
Mac 속도와 실제 모델 명령 품질은 사용자 컴퓨터에서 검증해야 한다.

## 바뀐 규칙

출시 맵은 팀당 28명: 전투 8명×2, 정찰6명, 지원6명. 초기 크레딧 +400.
기존 소형 학습/회귀 맵은 16명을 유지해 기존 학습 입력 계약을 보존한다.
병사는 이동 중에도 사격하며, 분대는 유효 사거리에서 정지한다.
기본 보병22m, 정찰18m, 지원27m. 시야와 벽의 차폐를 검사한다.
숲 속 표적은 명중률이 20% 감소한다. 탄약·공격 간격·확률 피해가 승패에 영향을 준다.
체력바, 사격선(적중 적갈색/빗나감 회녹색), 툴팁의 탄약·사거리·표적 ID 제공.
201 탐지 +20%(거점 주변), 202 순환 보너스 점수, 203 보급 +8/분.
모든 거점은 3명 이상으로 점령하며 점령20초/중립화15초, 100점 승리.
수송차는 무장하지 않는다. HQ는 가까운 빈 APC/HEL에 분대를 태워 거점으로 수송/하차한다.

## 반복 경기 / CPU 강화학습

규칙 HQ 무한 경기(완료 결과를 즉시 저장):
`uv run python -m engine.series --count 0`
중단은 Ctrl+C, 같은 명령으로 다음 seed부터 재개한다.

학습은 Linux CPU 환경에서 `uv sync --locked --extra learning` 후:
`uv run --extra learning python -m learning.continuous --rounds 0 --steps 256`
처음 점검은 `--rounds 1`. 각 라운드는 이전의 고정 상대와 PPO 학습 후
모델/NumPy 정책/상태를 저장한다. Ctrl+C로 종료하고 같은 명령으로 재개한다.
학습된 정책은 자동으로 강하다고 간주하거나 LLM HQ를 대체하지 않는다.
Intel Mac은 고정 torch 패키지가 없어 해당 학습 명령을 지원하지 않는다.
이전 평가 결과는 변경 전 규칙 기준으로, 새 규칙의 성능 근거로 사용할 수 없다.
