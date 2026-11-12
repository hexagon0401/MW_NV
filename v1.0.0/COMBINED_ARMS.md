> 최신 픽셀아트·상태창: [ART](docs/pixel-refinement/ART.md), 수송 수정: [TRAFFIC](docs/pixel-refinement/TRAFFIC.md).

# 제병협동 / 로컬 실행과 학습

현재 규칙은 `combined-arms-2`, 카탈로그는 `combined-arms-1`, 후보·정책 계약은 `tactics-1`이다.
출시 맵은 1024m, 팀당 64명(8명×8분대)과 차량10대다.
기존 256m 실험 환경과 구형 32차원 정책은 회귀·비교용으로 보존했다.

## Mac 실행

```bash
cd ~/MW_NV
git fetch origin
git switch dev/v1.0.0
git pull --ff-only
cd v1.0.0
```

처음 한 번 `brew install uv ollama`, 별도 터미널에서 `ollama serve`.
게임 터미널에서 `bash scripts/mac-local.sh`.
또 다른 터미널에서 `cd ~/MW_NV/v1.0.0/viewer && npm ci && npm run dev`.
브라우저: `http://127.0.0.1:5173/?mode=live`.

Ollama는 작은 대안 모델 `qwen3:0.6b`를 사용한다. 실제 모델 정보·digest는
`data/local-model-*`에 남는다. Qwen3.5 GGUF 후보의 미검증 상태는 유지한다.
Mac 실제 추론 품질·속도는 별도 확인이 필요하다.
모델 실패 시 알고리즘 HQ로 복구하고 판단 이유를 패널에 표시한다.
LLM 없이 검사하려면:

```bash
uv run --locked --extra server python -m server.live --hq rules --seed 1
```

## 성능 설정과 전투

권위 있는 자료는 `config/units.yaml`, `vehicles.yaml`, `weapons.yaml`이다.
보병의 크기는 12×20px(지원·대전차16×20), 기존 84cm 근접 충돌 기준을 유지한다.
UI 카탈로그·AI·피해 계산은 같은 설정을 읽는다. 툴팁에서 HP·탄약·사거리·
명중률·피해·간격·방호·속도·가격·수송 정원을 확인할 수 있다.

| 종류 | HP / 방호 | 속도 | 사거리 | 피해 / 간격 / 탄약 | 수송 |
|---|---|---|---|---|---|
| 보병 | 100 / 비장갑 | 1.6m/s | 22m | 11 / 2s / 30 | — |
| 정찰 | 80 / 비장갑 | 1.9m/s | 18m | 7 / 2.5s / 20 | — |
| 지원 | 110 / 비장갑 | 1.3m/s | 27m | 16 / 3s / 45 | — |
| 대전차 | 90 / 비장갑 | 1.4m/s | 100m | 140 / 8s / 6 | — |
| LUV | 150 / 비장갑 | 8m/s | — | 비무장 | 4 |
| APC | 350 / 경장갑 | 5.5m/s | — | 비무장 | 8 |
| IFV | 450 / 중장갑 | 5m/s | 90m | 35 / 1.5s / 120 | 8 |
| 전차 | 900 / 전차 장갑 | 4m/s | 150m | 180 / 6s / 30 | 0 |
| 자주곡사포 | 280 / 경장갑 | 3m/s | 100–420m | 90 / 15s / 18 | 0 |
| CH-47 | 300 / 항공(착륙 시 경장갑) | 11m/s | — | 비무장 | 16 |
| 보급차 | 180 / 비장갑 | 5m/s | — | 비무장·보급240 | 0 |

의무병80HP/1.6m/s, 공병90HP/1.4m/s는 비무장이다.
공병은 정지한 아군 차량 3m 이내에서 2초마다 HP10 수리(보급2·수리자원10).
보유 한도는 보병96·차량14, 초기 편성 별도 지급 후 자원1000C/티켓32/보급600.
초기 보급차 적재240은 초기 지급이며 추가 자원600과 별도다.
알고리즘은 손실 병종부터 초기 편성을 보충하고, 개별 구매 명령은 한도까지 허용한다.

| 탄종 | 비장갑 | 경장갑 | 중장갑 | 전차 | 비행 헬기 |
|---|---|---|---|---|---|
| 소총/기관총 | 1 | .1 | 0 | 0 | .25 |
| 기관포 | 1 | .7 | .35 | .1 | .25 |
| 로켓/전차포 | .4 | 1 | .85 | .7 | 0 |
| 곡사포 | 1 | .7 | .35 | .2 | 0 |

직사는 현재 시야·차폐·사거리·탄약을 검사하며 숲 표적 명중률은 ×0.8이다.
전차는 교전 거리에서 정지한다. 곡사포는 설치6초/철수4초, 비행3초,
산포8m/폭발12m이며 폭심에서 선형 감쇠한다. 아군도 같은 피해를 받는다.
현재 또는 10초 이내 관측한 좌표에만 발사하고 숨은 적을 추적하지 않는다.
탑승 차량 파괴 시 HP25 피해 후 합법 공간으로 비상 하차하며 공간이 없으면 전투불능.
잔해는 통행을 막지 않는다. 점령에는 하차 보병3명이 필요하다.

## AI와 정책

관측에서만 거리·HP·탄약·위협·예상 장갑 피해·보급·운송을 분석한다.
최대64개 후보, LLM에는 역할별 상위12개, 명령은 회차당 최대4개다.
명령 간 부대/탑승 차량·보급/크레딧/티켓 예약과 아군 근처 포격을 걸러낸다.
LLM은 후보 ID만 고르고 엔진이 다시 검증한다. 판단30초마다 시간 정지.
후보 점수와 이유는 알고리즘 근거이며 LLM의 자유 형식 설명으로 대체하지 않는다.

새 PPO는 1056차원(전역32+후보16×64), 행동65(후보64+종료), 128×128 MLP다.
한 회차 최대4개 지시 후 30초 진행한다. LLM은 학습 중 호출하지 않는다.
보상: 승/패 ±1, 점수차 변화×.01, 초기 편성 가치 대비 적·아군 손실차×.1.
Mac에서 PyTorch를 설치할 필요 없이 버전 검사된 NumPy 정책으로 추론한다.
정책이 없거나 호환되지 않으면 알고리즘 점수를 사용한다.

Linux CPU에서만:

```bash
uv sync --locked --extra dev --extra server --extra learning
uv run --extra learning python -m learning.continuous --root data/tactics-pool --rounds 1 --steps 64
# 명시적으로 반복 학습할 때 --rounds 0, 중단은 Ctrl+C, 같은 명령으로 재개
uv run --extra learning python -m learning.candidate_evaluate --policy data/tactics-pool/round-000000.npz --count 1
uv run python -m learning.results export --db data/results.sqlite --file data/results.jsonl
```

학습 seed0–49, 보류 평가10000–10099를 분리하고 평가는 양 진영 배치를 교대한다.
`.npz`와 JSONL 전적을 Mac의 `data/imported/`로 복사한 다음:

```bash
uv run python -m learning.results import --file data/imported/results.jsonl
MW_NV_POLICY=data/imported/round-000000.npz bash scripts/mac-local.sh
```

기존32차원 정책 폴더와 새 학습 폴더를 섞지 않는다. `--contract legacy`는 구형 실험용이다.
짧은 학습 통과는 학습 성능 향상의 근거가 아니다. 정책 자동 승격은 하지 않는다.

## 기록과 호환성

`/api/stats`는 로컬 `data/results.sqlite`를 읽는다. 전체 완료 경기와 양팀 승/패/무,
규칙·모드·정책·상대별 전적과 학습 step을 표시한다. 무승부 포함 전체 완료 경기로 승률을 계산한다.
학습·평가·하이브리드·규칙 경기를 구분하고 중단 경기와 중복 ID는 집계하지 않는다.
JSONL 가져오기는 전체 검증 후 트랜잭션으로 처리한다. 오류는 빈 전적과 구분한다.
학습 중 변하는 가중치는 training-run ID로, 고정 정책은 가중치 해시 ID로 표시한다.
체크포인트 JSON에는 training-run과 고정 정책 ID의 대응을 기록한다.

명령 번호0–12는 유지, 13표적 공격/14포격/15설치/16철수/17수리를 추가했다.
리플레이 엔진 문서는 version2와 규칙/카탈로그 버전을 검사한다.
구형 화면용 version1 리플레이는 계속 표시하며 없는 값은 —로 남긴다.
읽기 전용 관전이 엔진 상태나 RNG를 변경하지 않는지 회귀 검사한다.
전장 장식은 좌표 해시만 사용하며 엔진 난수와 분리한다.

실제 검증·스크린샷은 `docs/combined-arms/`에 있다. 배포하지 않는다.
