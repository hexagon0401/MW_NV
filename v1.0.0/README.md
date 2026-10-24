# MW-NV v1.0.0

현재 C01–C21의 작업카드 완료 조건을 구현한 로컬 headless 게임 엔진이다.
시드 기반 결정론, 명령 검증·팀별 큐, 지형/A*, 보병·분대 이동, 시야/추상 전투,
점령/점수/연장, 수송 차량·헬기·승하차, 보급/치료, 양팀 규칙 HQ를 제공한다.
로컬 LLM HQ, 리플레이 재생, 웹 관전, PPO는 다음 단계다.

## 설치·실행

Git과 [uv](https://docs.astral.sh/uv/getting-started/installation/)를 설치한 후:

```sh
git clone --branch dev/v1.0.0 https://github.com/hexagon0401/MW_NV.git
cd MW_NV/v1.0.0
uv sync --locked --extra dev
uv run --locked --extra dev python -m pytest -q
uv run --locked python -m engine.headless --seeds 1
uv run --locked python -m engine.headless --seeds 10 --paired --output /tmp/mw-nv-scores.json
```

Python 3.12가 없으면 uv가 관리형 Python을 준비한다. 최초 설치에 네트워크가
필요하며, 이후 경기는 모델·API 키·외부 서비스 없이 CPU에서 실행된다.
설치 후 `.venv/bin/python -m pytest -q`도 가능하다. 기존 clone은 작업을 보존한 뒤
`git pull --ff-only`, `uv sync --locked --extra dev`로 갱신한다.
검증 환경: Linux x86_64, Python 3.12.14. Intel Mac 실기 검증은 아직 하지 않았다.

## 실행 계약

- `Engine(WorldState(seed))`: 작은 128m 테스트 세계.
- `Engine(create_match(seed, swap=False))`: 대칭 256m Beta, 팀당 16인·APC/HEL/TRK.
- `Engine.submit_for(team, command)`: 외부 정책의 인증된 팀 번호와 명령 소유권 검사.
- `Engine.step(dt)`: 0.2초 고정 tick을 밀리초 정밀도로 누적하고 이번 호출의 이벤트 반환.
- `Engine.observe(team)`: 복사된 아군·현재 보이는 적·60초 이내 마지막 관측·팀 명령 상태.
- `RuleHQ.observe_and_issue(obs)`: 읽기 전용 관측에서 최대 4개 명령 생성.

명령은 원본 C.3 필드에 필수 정수 `cmd_id`, 선택 `priority`를 추가한다.
`EMBARK/HEAL/RESUPPLY`는 `target`에 차량/환자/보급 지점 ID를 사용한다.
`DISEMBARK/TRANSPORT/MOVE`는 `unit`과 미터 좌표 `arg0/arg1`을 사용한다.
JSON 명령의 미등록 필드·실수·불리언을 거부한다. `PURCHASE`는 enum만 있고
실행은 아직 `UNSUPPORTED_OP`로 거부한다. `Engine.submit`은 엔진 내부 테스트용이다.

기본 HQ는 30초마다 행동한다. 초기 편성 비용 787 credits/16 tickets와 트럭 적재
120 supply를 실제 차감한다. 팀당 잔액은 213 credits, 54 tickets, 180 supply다.
모든 수치는 가상의 아케이드 게임 값이다. 차량에 무장 동작은 없다.

## 검증·다음 작업

- `examples/team_swap_scores.json`: 10개 seed × 기본/위치 교환 = 20경기의 점수·해시.
- `examples/headless_match_summary.json`: 작은 테스트 세계의 경기 종료 요약.
- `IMPLEMENTATION_NOTES.md`: 구현 선택, 남은 전체 명세 항목 및 검증 한계.
- `STATE.md` → `DECISIONS.md` → 해당 작업 카드로 재개한다. 다음은 C21-L1 로컬 LLM 어댑터다.
- 실행 의존성 [PyYAML](https://github.com/yaml/pyyaml), 개발 의존성
  [pytest](https://github.com/pytest-dev/pytest)는 MIT 라이선스이며 버전은 잠금 파일에 고정한다.
