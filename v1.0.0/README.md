# MW-NV v1.0.0

현재 구현: **C01 최소 부트스트랩**. 128×128m 지도와 0.2초 tick 설정을
읽고 검증한다. 게임 실행·LLM·관전·학습은 아직 구현하지 않았다.

## 내려받아 설치

Git, Python 3.12와 [uv](https://docs.astral.sh/uv/getting-started/installation/)가 필요하다.
uv는 별도로 설치하고, 아래 명령은 저장소를 둘 디렉터리에서 실행한다.

```sh
git clone --branch dev/v1.0.0 https://github.com/hexagon0401/MW_NV.git
cd MW_NV/v1.0.0
uv sync --locked --extra dev
uv run --locked --extra dev python -m pytest -q
```

이미 내려받았다면 해당 브랜치에서 `git pull --ff-only` 후 `uv sync`부터 실행한다.
최초 설치에는 패키지 다운로드가 필요하다. 가상환경 구성 후 같은 환경에서는
재설치 없이 `.venv/bin/python -m pytest -q`로 테스트할 수 있다.
Python 3.12가 없으면 uv가 지원하는 관리형 Python을 사용한다.

Intel Mac mini 2018·RAM 32GB를 우선 대상으로 한다. 실제 검증 환경은
`STATE.md`에 기록하며, Linux 테스트가 Mac 검증을 대신하지는 않는다.
현재 검증 도구: CPython 3.12.14, uv 0.12.23 (Linux x86_64).

## 설정 읽기

위의 `v1.0.0` 디렉터리에서 실행한다.

```sh
uv run --locked python -c 'from engine.config import load_game_config; print(load_game_config("config/game.yaml"))'
```

결과: `GameConfig(map_width_m=128, map_height_m=128, tick_s=0.2)`.
`load_game_config(path)`는 UTF-8 YAML을 읽어 불변 `GameConfig`를 반환한다.
지도 폭·높이는 양의 정수, tick은 유한한 양수여야 하며 위반 시 `ValueError`다.
파일 읽기 오류와 잘못된 YAML 문법은 원래 예외를 그대로 전달한다.
파일 경로는 호출자가 지정하므로 엔진은 현재 디렉터리에 의존하지 않는다.

## 의존성과 진행 방식

- 실행 의존성: [PyYAML 6.0.3](https://github.com/yaml/pyyaml) (MIT).
- 개발 의존성: [pytest 8.4.2](https://github.com/pytest-dev/pytest) (MIT).
- `pyproject.toml`과 `uv.lock`이 버전을 고정한다. 필요한 단계에서만 의존성을 추가한다.
- `STATE.md` → `DECISIONS.md` → 원본 A절과 현재 Cxx 카드 순서로 확인한다.
- Cxx 하나씩 테스트·커밋·push하고 종료한다. 현재 다음 기능은 C02 엔티티 타입이다.
- 양팀 로컬 LLM HQ는 C21-L1/L2에서 구현한다. 모델 다운로드나 추론 서버는 C01에 필요 없다.
- 비밀값·모델·실행 데이터는 커밋하지 않는다. 외부 유료 자원이나 배포를 자동 생성하지 않는다.
