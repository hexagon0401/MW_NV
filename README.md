# MW-NV

MW-NV는 결정론적 전장 시뮬레이션, AI 지휘, 강화학습과 픽셀아트 관전을 결합한 실험 프로젝트입니다. 두 진영이 병력·차량·수송·보급을 운용하며, 엔진이 이동과 전투를 처리하고 AI는 관측 가능한 정보로 지휘 후보를 선택합니다.

[관전 사이트](https://mw-nv.pages.dev/) · [운영 대시보드](https://mw-nv.pages.dev/dashboard/) · [현재 작업 상태](v1.0.0/STATE.md) · [설계 결정](v1.0.0/DECISIONS.md)

> 이 프로젝트는 개발 중입니다. 문서에 있는 과거 실험 결과와 현재 운영 설정은 다를 수 있습니다. 실제 학습 진행 여부는 대시보드의 최신 갱신 시각과 실행 상태를 확인하세요.

## 주요 기능

- **결정론적 엔진:** 고정 0.2초 tick과 seed를 사용해 이동, 시야, 전투, 점령, 수송, 보급을 처리합니다.
- **제병협동:** 보병과 역할별 분대, 수송 차량, 장갑차, 전차, 곡사포, 헬리콥터 및 대공 수단을 운용합니다. 성능은 게임 밸런스를 위한 수치입니다.
- **세 가지 경기 방식:** 2번 맵 고지점령, 3번 맵 섬멸, 4번 맵 깃발 탈취·귀환을 지원합니다. 혼합 학습은 섬멸 → 깃발 → 고지점령 순서로 완료 학습 경기 10개씩 순환하도록 구성되어 있습니다.
- **관전:** 완료 경기 리플레이를 재생하고, 최근 3경기·양팀 상태·명령·전투 효과와 전적을 확인합니다. 진행 중인 로컬 경기는 별도 서버에서 관전할 수 있습니다.
- **학습·평가:** 독립적인 PPO1·PPO2와 과거 정책/규칙 상대를 사용하고, 학습 경기와 고정 정책 평가를 구분해 기록합니다. 정책 보관과 복구용 체크포인트를 지원합니다.
- **AI 지휘:** 각 팀의 관측을 분리합니다. 규칙 기반 지휘와 로컬 LLM 또는 NVIDIA NIM 연결을 지원하며, 엔진이 명령의 유효성을 검증합니다. 실행 방식과 설정에 따라 AI 연결과 실패 시 대체 동작이 달라집니다.

## 빠른 시작

### 요구 사항

- Git, Python **3.12**, [uv](https://docs.astral.sh/uv/)
- Node.js **22.12 이상 또는 24**와 npm: 관전 화면 개발용
- Linux CPU: PPO 학습용. Intel Mac은 로컬 관전과 NumPy 정책 추론을 우선 대상으로 하며 실기 성능은 별도 확인이 필요합니다.

```bash
git clone --branch dev/v1.0.0 https://github.com/hexagon0401/MW_NV.git
cd MW_NV/v1.0.0
uv sync --locked --extra dev --extra server --extra inference
uv run --locked --extra dev pytest -q
uv run --locked python -m engine.headless --seeds 1 --release
```

`dev/v1.0.0`은 개발 브랜치입니다. 원격 저장소의 실제 기본 브랜치와 배포 버전은 GitHub에서 확인하세요. 프로젝트 코드는 `v1.0.0/` 아래에 있습니다.

### 로컬 리플레이 관전

첫 번째 터미널에서:

```bash
cd MW_NV/v1.0.0
uv sync --locked --extra server --extra inference
uv run --locked python -m engine.viewer_export
mkdir -p data
cp viewer/public/demo.json data/demo.view.json
uv run --locked --extra server python -m uvicorn server.app:app --host 127.0.0.1 --port 8000
```

두 번째 터미널에서:

```bash
cd MW_NV/v1.0.0/viewer
npm ci
npm run dev
```

Vite가 터미널에 출력하는 로컬 주소로 접속합니다. API와 개발 서버를 종료하려면 각각의 터미널에서 `Ctrl+C`를 누릅니다. 로컬 진행 경기와 SSE 관전은 [서버 안내](v1.0.0/server/README.md)를 참고하세요.

### 검사

```bash
cd MW_NV/v1.0.0
uv run --locked --extra dev pytest -q
npm --prefix viewer ci
npm --prefix viewer test
npm --prefix viewer run build
```

학습 관련 검사는 Linux에서 `uv sync --locked --extra dev --extra server --extra learning`으로 선택 의존성을 설치한 뒤 실행합니다. 설치되지 않은 선택 기능의 검사 결과와 전체 통과 결과를 구분하세요.

## 경기 규칙

| 모드 | 목표 |
| --- | --- |
| 고지점령 | 거점을 확보하고 점수를 획득합니다. |
| 섬멸 | 상대의 전투 티켓 또는 전투력 회복 가능성을 소진시킵니다. 제한 시간에는 초기 대비 남은 전투 티켓 비율로 판정합니다. 구매용 크레딧과 전투 티켓은 별개입니다. |
| 깃발 탈취·귀환 | 보병으로 상대 깃발을 확보하고 아군 본진으로 반납합니다. 탈취 점수와 제한 시간 판정도 적용됩니다. |

실제 승패 판정은 엔진과 해당 시나리오 설정이 기준입니다. 규칙 버전이 다른 리플레이를 엔진에서 재실행할 때는 호환성 확인이 필요합니다. 자세한 편성·전투 규칙은 [제병협동 문서](v1.0.0/COMBINED_ARMS.md)와 [다중 모드 문서](v1.0.0/docs/multi-mode/README.md)를 확인하세요.

## 학습과 운영 구조

```text
팀별 제한 관측 → 전술 후보 생성 → PPO 정책 선택 → 엔진 검증·실행
                         ↘ NIM 교사 표본은 별도 모방 학습에 사용
완료 경기·체크포인트 → 비공개 저장소/보관 → 관전 사이트·대시보드
```

현재 설계는 PPO1과 PPO2를 별도의 정책으로 유지합니다. NIM 교사 응답은 별도 모방 데이터로 취급하며 PPO의 실제 행동 경험과 구분합니다. 고정된 과거 정책과의 평가, 다른 seed·진영에서의 평가를 통해 진척을 확인합니다. 단순히 경기 수나 승률이 늘었다는 사실만으로 전략 향상이나 새로운 맵에 대한 일반화를 보장하지 않습니다.

고지점령 기준 모델은 혼합 학습 이전의 1,189경기·세대 2748 시점에 별도로 보존했습니다. [보관 기록](v1.0.0/docs/capture-baseline-1189.md)과 [GitHub Release](https://github.com/hexagon0401/MW_NV/releases/tag/capture-specialists-1189-g2748)를 참고하세요. 입력 계약이 다른 혼합 정책으로 이관할 때는 각 모델을 독립적으로 증류하고 새 critic·optimizer를 사용합니다.

Cloudflare Pages는 관전 화면과 API를 제공하며 PPO를 실행하지 않습니다. 경기와 학습은 별도 CPU 실행 환경에서 진행하고 결과를 Supabase 비공개 Storage에 발행합니다. Codex 환경의 백그라운드 프로세스는 대화 종료 후에도 환경이 살아 있으면 계속될 수 있지만, **환경 종료 후 상시 실행은 보장되지 않습니다.** 외부 Workers 기반 자동 감시 적용은 현재 보류 상태입니다.

## 저장소 구조

| 경로 | 내용 |
| --- | --- |
| `v1.0.0/engine/` | 게임 상태, 규칙, 이동·전투, 리플레이와 화면용 데이터 |
| `v1.0.0/agents/` | 팀 관측을 이용한 지휘 후보 및 HQ 로직 |
| `v1.0.0/learning/` | PPO, 자체 대전, 평가, 전적과 체크포인트 |
| `v1.0.0/viewer/` | PixiJS 관전 화면, 대시보드, Pages 함수 |
| `v1.0.0/server/` | 로컬 API, 실시간 관전과 운영 제어 |
| `v1.0.0/cloud/` | 클라우드 저장·연동 코드 |
| `v1.0.0/config/` | 시나리오, 카탈로그 및 업데이트 명세 |
| `v1.0.0/docs/` | 단계별 설계, 검증 결과와 운영 기록 |

## 문서와 작업 재개

- [프로젝트 상세 안내](v1.0.0/README.md) · [제병협동](v1.0.0/COMBINED_ARMS.md) · [다중 모드](v1.0.0/docs/multi-mode/README.md)
- [대시보드](v1.0.0/docs/dashboard/README.md) · [업데이트 준비·적용](v1.0.0/docs/releases/README.md)
- [적응형 실행과 복구](v1.0.0/docs/adaptive-acceleration/README.md) · [장시간 운영 설계](v1.0.0/docs/runtime-continuity.md)
- [서드파티 의존성과 라이선스](v1.0.0/THIRD_PARTY.md)

일부 세부 문서는 작성 당시 상태를 보존하므로 오래된 실행 예시나 배포 전 설명이 포함될 수 있습니다. 작업을 이어갈 때는 `v1.0.0/STATE.md`와 `DECISIONS.md`의 최신 항목부터 확인하세요.

모델 파일, 가상환경, API 키와 대형 실행 로그는 Git에 넣지 않습니다. 외부 서비스의 비밀키는 환경 설정의 안전한 저장소에 입력하고 채팅이나 공개 문서에 포함하지 마세요.

## 라이선스

프로젝트 코드는 [MIT License](LICENSE)를 따릅니다. 외부 라이브러리·폰트·모델에는 각각의 라이선스가 적용됩니다.
