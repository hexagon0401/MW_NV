# MW-NV v1.0.0

결정론적 픽셀 워게임 엔진과 읽기 전용 관전 화면이다. 보병·분대·차량 수송·시야·추상 전투·
점령·보급과 규칙/로컬 LLM HQ, 리플레이, CPU PPO 학습·평가를 구현했다.
**실제 LLM 모델, 외부 비공개 배포, Intel Mac 실기 검증은 아직 완료하지 않았다.**
현재 상태와 필요한 조치는 RELEASE_STATUS.md, SETUP_ACTIONS.md를 참고한다.

## Intel Mac에서 내려받아 실행

Python 3.12, uv, Node 22.12 이상(또는 24), Git이 필요하다.

```sh
git clone --branch dev/v1.0.0 https://github.com/hexagon0401/MW_NV.git
cd MW_NV/v1.0.0
uv sync --locked --extra dev --extra server --extra inference
uv run --locked --extra server python -m pytest -q
uv run --locked python -m engine.headless --seeds 1 --release
```

Linux 전체 검사에는 추가로 --extra learning을 설치한다. 학습 의존성이 없는 환경에서는
해당 선택 테스트만 skipped로 표시된다. 핵심 엔진 테스트는 계속 실행된다.
Intel Mac에서는 최신 PyTorch 학습 대신 NumPy 정책 추론을 사용한다.
의존성은 uv.lock과 viewer/package-lock.json으로 고정한다.

## 관전

```sh
python -m engine.viewer_export
cp viewer/public/demo.json data/demo.view.json
python -m uvicorn server.app:app --host 127.0.0.1 --port 8000
```

다른 터미널의 v1.0.0/viewer에서 npm ci 후 npm run dev를 실행한다.
드래그/휠로 지도 이동·확대, 0.5/1/2/4배 재생, 경기 선택과 읽기 전용 HUD를 제공한다.
GET /matches, /matches/{id}, /events, /snapshot은 완료 경기만 반환한다.
실행법·API 상세는 server/README.md에 있다. npm test와 npm run build로 프런트엔드를 검사한다.
실제 Chromium 검사는 viewer에서 node scripts/browser-smoke.mjs를 사용한다.
CHROMIUM_PATH와 VIEWER_URL을 지정해 브라우저 경로와 테스트 대상을 바꿀 수 있다.

## 로컬 LLM·리플레이·학습

- tools/README.md: 고정 버전 llama-server 빌드, 검증된 GGUF 다운로드, 50개 상태 측정.
- python -m engine.local_match: 1024m 지도에서 양팀 로컬 LLM HQ 실행, 실패 시 규칙 HQ 복구.
- 모델은 loopback 서버 하나를 공유하며 30 sim seconds마다 결정한다. 응답 중 게임 시간은 멈춘다.
- engine.replay는 JSON 체크포인트와 명령/시간 저널로 재생하며 모델을 재호출하지 않는다.
- learning/README.md: 제한된 CPU MaskablePPO 학습, 동결 상대와 3개 정책 풀, 독립 holdout 평가.
- examples/EVALUATION.md: 실제 비교 결과. 성능 향상을 가정하지 않고 규칙 HQ를 기본으로 유지했다.
- 모델·가중치·비밀키·실행 로그는 Git에 넣지 않는다. data/와 models/는 로컬 산출물이다.

## 명령 계약과 재개

고정 정수 opcode는 원본 C절을 따른다. cmd_id는 팀별 정수이며 priority는 선택이다.
PURCHASE는 arg0=0..9(INF/REC/SUP/MED/ENG/LUV/APC/IFV/HEL/TRK), target=아군 HQ다.
Engine.submit_for는 외부 정책의 팀을 인증하고, Engine.step은 0.2초 고정 tick을 실행한다.
1024m 모드와 256m 학습 모드는 같은 엔진을 사용한다.
STATE.md → DECISIONS.md → 현재 작업 카드 순서로 재개한다.
