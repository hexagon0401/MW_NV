# DECEPTION CTRL — v1.0.0 Codex Execution Plan

> **작성 기준:** 2026-10-24 (KST)  
> **용도:** Codex에 직접 전달할 실행 명세. 이전 `DECEPTION_CTRL_v1.0.0_MASTER_PLAN.md`의 개발 일정·구현 우선순위를 이 문서가 **대체**한다. 기존 Master Plan은 비전/참조 자료로만 필요할 때 부분 열람한다.  
> **실행 상태:** 계획서. 아래 코드·명령·테스트는 구현 완료를 뜻하지 않는다.  
> **대상 환경:** Mac mini 2018 Intel Core i7 / RAM 32GB, ChatGPT Plus/Codex 사용, 소규모 독립 개발.  
> **범위:** 두 AI HQ의 명령형 픽셀 워게임 v1.0.0. 모든 소스와 버전별 데이터는 리포지토리의 **`v1.0.0/` 아래** 저장한다.

---

## A. Codex가 매 사이클 읽을 1페이지 규칙

**목표는 한 번에 게임을 만드는 것이 아니라, 작은 완성 단위를 지속적으로 검증해 1.0.0을 만드는 것이다.**

1. **작업 범위:** 한 사이클 = 아래 `C01–C36` 중 **1개 작업만** 구현. 새로운 기능을 추가하기 전에 해당 작업의 `DoD`(완료 조건)를 읽고, 통과하면 즉시 중단한다. 하나의 사이클에서 여러 작업을 합치지 않는다.
2. **파일 범위:** 모든 기능 코드·테스트·설정·체크포인트·웹 자산을 `v1.0.0/` 하위에만 생성한다. `.gitignore`, 저장소 루트 `README.md`처럼 정말 필요한 공통 파일은 예외이며 최소 변경. 기존 사용자 변경사항 보존.
3. **AI = HQ:** AI 모델은 **상황 판단 및 정형화된 명령 생성만 한다.** 보병/차량 이동, 경로탐색, 적 감지, 전투, 재보급, 점령 판정은 **게임 엔진 코드**가 처리한다. 개별 유닛마다 LLM을 호출하지 않는다.
4. **차량 = 수송:** 1.0.0의 탈것은 **이동·탑승·하차·연료·보급 수송만** 구현. APC/IFV라도 차량 무장·사격·공격 AI·물리 탄도는 없다.
5. **보병:** 캐릭터마다 크기·속도·시야·게임형 공격 능력치를 YAML로 정의하고, 명령을 받아 FSM으로 이동/행동한다. 현실 무기 제원이나 실제 전술을 모델링하지 않는다.
6. **토큰 최적화:** 작업에 필요한 **하나의 명세 절과 최소 관련 파일만** 읽는다. 이전 80KB Master Plan 전체를 매번 컨텍스트에 넣지 않는다. 테스트 로그는 실패 요약/관련 줄만 보여준다.
7. **사용 한도:** 사용자의 목표는 **Plus 한도의 최대 90%까지만 사용, 최소 10% 여유 보존**. 다만 Codex는 고정된 'Plus 토큰 총량'을 보장하지 않으므로 실제 사용량 UI가 없으면 임의 숫자를 추정하지 않는다. 작업·도구 호출 상한 및 조기 정지 규칙을 보조 수단으로 사용한다.
8. **하루 3회:** 원칙적 작업 창은 **08:00 / 14:00 / 20:00 KST**(6시간 간격)로 계획한다. 이것은 실행 **계획**이지 자동 예약이 아니다. 사용자가 Codex를 열거나 별도 승인된 스케줄러가 실행해야 한다. 공식 Plus 사용량은 5시간 창 및 다른 사용과 공유될 수 있으므로 각 회차 직전 `Codex /status` 또는 ChatGPT Usage를 확인한다.[O1][O2]
9. **검증:** 코드가 조금이라도 바뀌면 해당 범위의 자동 테스트를 실행한다. 완료 보고는 `변경 파일 / 실행한 테스트 / 통과 여부 / 남은 결함 / 다음 사이클 ID`만 남긴다.
10. **종료:** 기능 DoD 통과, 사용량 90%에 근접, 테스트 불안정, 권한/외부 결제 요구, 범위 확대 필요 중 하나가 발생하면 안전하게 중단하고 상태를 기록한다.

### A.1 매 사이클 적용할 실제 작업 상한

| 통제 항목 | 기본 상한 | 초과할 때 |
|---|---|---|
| 기능 | **1개**(Cxx 하나) | 다음 사이클로 이관 |
| 소스 파일 | 신규/수정 최대 **3개**(테스트/설정 제외) | 범위 재분해 후 사용자에게 보고 |
| 기능 코드 diff | **대략 250줄 이하 권장** | 테스트를 포함한 이유와 영향 범위를 기록, 불필요한 리팩터링 금지 |
| 새 외부 라이브러리 | **1개 이하** | 실제 필요성과 대안 검토. 설치/네트워크 승인이 필요하면 중단 |
| 외부 서비스 작업 | 해당 기능 단계 전에는 **0건** | 클라우드/결제/배포를 임의 실행하지 않음 |
| 모델 추론 호출 | 핵심 엔진 구현 중 **0건** | 먼저 규칙 기반 HQ로 게임 성립 검증 |
| 진행 기록 | `v1.0.0/STATE.md` 1개 | 성공·보류·다음 작업 간단히 업데이트 |

코드 줄 수는 **토큰 사용량과 동일한 측정치가 아니다.** 작업 확산을 막는 프로젝트 관리상의 상한이다. 작은 버그 수정은 굳이 250줄을 채우지 않는다.

### A.2 세션 시작 체크리스트

1. `v1.0.0/STATE.md`에서 현재 미완료 Cxx 확인(파일 없으면 C01).
2. `git status --short`로 사용자 변경사항·직전 작업 상태 확인.
3. `CODEX_EXECUTION_PLAN.md`의 **A절 + 현재 Cxx 작업 카드**만 읽고 나머지 긴 구간 스킵.
4. 이미 존재하는 엔진 타입/유닛 설정만 최소 범위로 열람.
5. 변경 → 관련 테스트 → 짧은 요약 → `STATE.md` 업데이트. 사용자가 요청하지 않으면 자동 배포/긴 훈련 시작 안 함.

### A.3 사용자가 Codex에 입력할 기본 프롬프트

```text
DECEPTION CTRL v1.0.0의 다음 1개 개발 사이클만 수행해줘.
프로젝트 파일은 모두 v1.0.0/ 하위에 둬.
v1.0.0/CODEX_EXECUTION_PLAN.md의 A절과 STATE.md, 그리고 지금 진행할 Cxx 카드만 확인해.
한 사이클에 한 기능만 구현하고 테스트해. 다른 단계 선행 구현 금지.
AI는 HQ 명령 생성기이며, 유닛의 실제 이동·전투·수송은 결정론적 게임 엔진이 담당한다.
새 라이브러리/외부 서비스 설치가 필요하거나 사용량이 90%에 근접하면 중단하고 보고해.
완료 시 변경 파일, 테스트 결과, 미해결 사항, 다음 Cxx를 10줄 내로 요약하고 STATE.md를 갱신해.
```

---

## B. Plus 한도와 하루 3회 운영 방법

### B.1 '90% 토큰'의 정확한 의미

- Codex Plus는 사용자에게 언제나 일정한 **하루 N토큰**을 주는 방식이라고 단정할 수 없다. 요청 규모·제품·모델·공유 사용량·정책에 따라 실제 사용 한도가 달라진다.[O1]
- 이 문서에서 **90%**는 모델 컨텍스트 90%를 억지로 채우는 목표가 아니라, **UI에서 확인 가능한 현재 사용 한도의 약 90%를 넘기지 않는 상한(10% 비상 예비)**이다.
- 08:00/14:00/20:00은 6시간 간격으로 5시간 사용량 창과 겹침을 줄이려는 제안이다. 공식 리셋 보장 시각이 아니므로 매번 사용 현황을 확인한다.
- **사용량을 수치로 확인할 수 없으면** `90% 소진`을 주장하지 않는다. 그때는 Cxx 하나 완료 또는 약 30–45분 이내 종료 같은 **작업 예산**으로 대신한다.
- 사용자의 다른 ChatGPT/Work/Codex 활동이 한도에 영향을 줄 수 있다. 따라서 하루 3회는 목표 상한이며, 남은 사용량이 부족하면 해당 회차를 건너뛰고 `STATE.md`에 기록한다.

### B.2 일일 3사이클 표준 루틴

| 회차 | 권장 KST | 목적 | 토큰 절약 방식 | 종료 조건 |
|---|---|---|---|---|
| **Cycle AM** | 08:00 | 전날 실패 재현 및 작은 핵심 구현 | 코드 읽기 범위 최소화, 실패 테스트 우선 | 1개 Cxx DoD 통과 |
| **Cycle PM** | 14:00 | 다음 연결 기능 구현 | 필요한 타입만 확인, Master Plan 재열람 금지 | 1개 Cxx DoD 통과 |
| **Cycle Night** | 20:00 | 기능 확장 또는 테스트/리플레이 검증 | 실패 로그 요약, 상태 정리 | 1개 Cxx DoD 또는 상태만 저장 |

**권고 시간 배분:** 각 회차 작업 시작 5분 상태 점검 → 20~30분 코드/테스트 → 마지막 5분 정리. 이는 예시이며 계정 사용량을 대신 측정하지 않는다. 세 회차를 전부 자동 실행하도록 계정 비밀키를 저장하거나 한도를 우회하지 않는다.

### B.3 실패 및 한도 대응

`PASS`: 테스트 통과 후 종료.  
`PARTIAL`: 미완료 코드/실패 테스트와 원인을 기록, 다음 회차에 같은 Cxx 이어서 진행.  
`BLOCKED`: 인증·접근권한·결제·의미 있는 설계 선택이 필요하면 사용자 질문.  
`BUDGET_STOP`: 현재 회차 한도 부족 시 파일 무리하게 수정하지 말고 현 상태·다음 명령만 기록.

**재시도:** 같은 실패 테스트를 수정 없이 3회 이상 반복 실행하지 않는다. 실패 원인을 점검하고 작업 범위를 줄인다. 린트·타입체크·단위테스트는 전체 저장소가 아니라 변경된 모듈 우선.

---

## C. 1.0.0 설계 동결 — AI와 엔진의 역할 분리

### C.1 최상위 구조

```text
  TEAM A HQ POLICY                     TEAM B HQ POLICY
  (읽기 전용 관측)                      (읽기 전용 관측)
        |                                      |
        v                                      v
   COMMAND_A[]                           COMMAND_B[]
        \                                      /
         -> ACTION VALIDATOR -> COMMAND QUEUE
                                     |
                                     v
                          DETERMINISTIC GAME ENGINE
                  movement | transport | sight | combat
                      capture | logistics | scores
                                     |
                          immutable EVENT LOG
                           /             \
                    OBSERVATION_A    OBSERVATION_B
```

`POLICY`는 명령만 반환한다. `GAME ENGINE`은 모든 명령을 검증하고 실행한다. AI가 `MOVE`를 선택했다고 해서 AI 코드에서 `x += velocity`를 실행하지 않는다.

### C.2 세 가지 실행 빈도

| 계층 | 간격(시뮬레이션 시간) | 수행 |
|---|---:|---|
| 엔진 물리 tick | **0.2 s** | 좌표, 충돌, 시야, 추상 전투, 점령 게이지, 태스크 진행 |
| HQ 정책 tick | **30 s** | 상태를 한 번 보고 최대 4개의 높은 수준 명령 출력 |
| 선택적 SLM 조언 | 게임당 **0–2회** | 전체 전략 간단 평가/요약. 게임 진행 필수 조건 아님 |

45분 게임 기준 HQ 정책 tick은 팀당 90번이다. **90번은 소형 정책망 추론**이며 **LLM 텍스트 생성 90회를 의미하지 않는다.** 학습 단계에서도 이 구분을 유지한다. 즉 한 에피소드에서 언어모델 가중치가 업데이트되는 일은 없다.

### C.3 명령 데이터 계약 v1

```json
{
  "v": 1,
  "tick": 150,
  "team": 0,
  "op": 2,
  "unit": 41,
  "arg0": 301,
  "arg1": 456,
  "target": 0,
  "ttl": 600
}
```

필드 고정형 정수 사용. `team`: `0=A, 1=B`; `tick`: 현재 0.2초 엔진 tick; `unit`: 팀 소유 unit/group ID; `arg0/arg1`: op에 따라 목적지 **미터 정수** 또는 vehicle ID; `ttl`: 만료까지의 **엔진 tick 수**. 예시의 `op=2(MOVE)`는 unit 41을 (301,456)m로 보내라는 **추상 명령**. 게임 엔진이 경로를 선택한다.

| op 코드 | 이름 | 의미/필수 데이터 | AI가 하지 않는 일 |
|---:|---|---|---|
| 0 | WAIT | 인자 없음 | 시간마다 경로 재계산 |
| 1 | HOLD | unit/group ID | 물체 위치를 직접 붙잡기 |
| 2 | MOVE | `unit, x, y` | A* 경로·가속/충돌 계산 |
| 3 | CAPTURE | `unit, objective_id` | 점령 게이지 강제 변경 |
| 4 | DEFEND | `unit, objective_id` | 개별 발사/조준 타이밍 |
| 5 | EMBARK | `unit/group, carrier_id` | 승차 순서·좌석 배정 |
| 6 | DISEMBARK | `carrier_id, x, y` | 하차 개별 좌표·충돌 계산 |
| 7 | TRANSPORT | `carrier_id, destination` | 차량 자체 이동물리/연료 감소 |
| 8 | RESUPPLY | `unit/group, supply_node_id` | 보급 수량·거리·대기열 처리 |
| 9 | HEAL | `medic_id, friendly_id` | 치료 쿨다운·효과 적용 |
| 10 | RETREAT | `unit/group, friendly_xy` | 후퇴 경로·도착 판정 |
| 11 | PURCHASE | `unit_type, spawn_site` | 금액 차감·생성 타이머/좌표 |
| 12 | CANCEL | `command_id` | 취소 시 엔진 상태 롤백 |

**관찰 권한:** A는 B의 숨겨진 부대를 읽지 못한다. `ENGAGE_VISIBLE`은 엔진 내 자동 반응으로 두고 HQ 별도 행동으로 강제하지 않는다. 정체불명 `target`은 무효 처리.

### C.4 명령 유효성

모든 명령에 대해: `schema ok → unit exists → owner matches → target bounds → task compatible → cooldown → supply/capacity → queue enqueue`. 거절 시 `INVALID_TARGET`, `FOREIGN_UNIT`, `NO_CAPACITY`, `NO_FUEL`, `ILLEGAL_STATE`, `EXPIRED`, `UNKNOWN_OP` 등의 명확한 오류를 다음 HQ 관측에서 제공. 중복 명령은 `cmd_id` 기반 멱등 처리.

### C.5 엔진 전체 구조의 시간 분리

- `GameState`는 Python 자료형/배열/데이터 테이블만 사용한다. PixiJS와 Supabase 호출 금지.
- `step(dt)` 호출은 완전히 내부 계산으로 완료되어야 한다. AI 모델이나 클라우드 응답을 기다리지 않는다.
- 엔진은 최신 명령을 **큐에 쌓고** 해당 tick에 해당하는 작업을 진행한다.
- 결과는 `events[]`와 `observation_A/B`로 반환한다. UI는 이벤트를 그리기만 한다.

---

## D. 픽셀 전장과 좌표 — 변경 불가 기본 규칙

### D.1 지도 스케일

- **최종 전장** `1024 × 1024 m`.
- **렌더 스케일** 1m × 1m 정사각형을 `3 × 3px`로 표현, 전체 배경 `3072 × 3072px`.
- **내부 물리 좌표** 정수 cm 권장(예: `x_cm=30100`), 렌더 시 `(x_cm/100) × 3 × zoom`.
- **전역 경로탐색** 4m 단위 grid(`256 × 256` 노드), 보병 로컬 회피는 1m 공간에서 처리.
- **렌더 청크** 128 × 128m(`384 × 384px`) × 전체 8×8 청크.
- 실제 게임 상태의 모든 픽셀을 매 tick 검사하는 방식 금지.
- `AI observation`은 격자 1,048,576개 전체가 아닌 **최대 32~128개 개체 요약 + 점령/보급 상태**만 포함한다.

### D.2 단계별 전장 확대

| 단계 | 전장 | 쓰는 목적 | 구현 여부 |
|---|---|---|---|
| World Alpha | 128 × 128m | 유닛/명령/유효성/재현성 검증 | C01–C09 필수 |
| World Beta | 256 × 256m | 시야/전투/거점/수송 검증 | C10–C22 필수 |
| World Release | 1,024 × 1,024m | 점령 3개·차량/보급·관전 | C23 이후 |

확대할 때 같은 좌표계·단위·명령 스키마를 유지하고 지도 크기만 config로 바꾼다. 매 단계 세계 전체를 다시 작성하지 않는다.

### D.3 필수 지도 오브젝트

| 오브젝트 | 중심(1024m 릴리스 기준) | 크기/기능 | 초기 구현 범위 |
|---|---|---|---|
| A HQ | `(96,512)` | 72×72m, A 생성·재보급 | 회복·생성 구역만 |
| B HQ | `(928,512)` | 72×72m, B 생성·재보급 | 반사 대칭 |
| North Tower | `(512,224)` | 점령 구역 반경 42m, 시야 +20% | 점령/시야 이벤트 |
| Central Plaza | `(512,512)` | 점령 구역 반경 46m, 기본 Hot Zone | 거점 점수 |
| South Depot | `(512,800)` | 점령 구역 반경 42m, 보급 재생 | 거점/보급 |
| Hospital A/B | `(304,640)`, `(720,640)` | 각각 24×30m, MED 치료 허브 | 추가 회복 계수 |
| Observation tower A/B | `(304,320)`, `(720,320)` | 각각 12×12m, 정찰 시야 보너스 | 객체/시야 |
| Garage A/B | `(176,512)`, `(848,512)` | 32×26m, 수송차 출발 | 스폰/재보급 |
| Helipad A/B | `(152,416)`, `(872,416)` | 38×38m, 헬기 착륙 | 착륙 검증 |

지도는 **좌우 거울 대칭**으로 생성한다. 각 거점은 양 HQ로부터의 최단 이동 비용 차이를 5% 이내로 유지(설계 목표). 점령 거점과 병원은 실제 병원·도시와 무관한 게임 자산이다.

### D.4 타일 타입 고정

`0=GRASS`, `1=ROAD`, `2=FOREST`, `3=WALL`, `4=BUILDING_INTERIOR`, `5=SHALLOW_WATER`, `6=DEEP_WATER`, `7=BRIDGE`, `8=OBJECTIVE`, `9=OBSTACLE`.

- 보병은 `GRASS, ROAD, FOREST, BUILDING_INTERIOR, SHALLOW_WATER, BRIDGE, OBJECTIVE` 통과, 장애물은 충돌 범위/조건부 우회.
- 지상 차량은 `ROAD, GRASS, BRIDGE, OBJECTIVE`만 기본 통과. 산림·건물 내부·물·벽은 불가.
- 헬기는 지상 타일 차폐를 받지 않고 `NO_FLY` 지형/맵 경계를 검사. 착륙은 허가된 `HELIPAD` 또는 10×10m 무장애 평지에서만.
- 길찾기 실패 시 `PATH_NOT_FOUND` 이벤트, 30초 후 HQ 재계획. 적이나 장애물 때문에 매 0.2초 A* 재시작하는 일 없음.

---

## E. 보병/캐릭터 확정 규격 — 1.0.0

### E.1 픽셀 크기와 실제 판정 크기를 구분

- **병사 1명 = 엔진 Entity 1개**. 개별 병사에게 AI 모델을 할당하지 않는다.
- **물리 충돌 점유:** 1×1m의 논리 셀(반경 0.42m 원형으로 충돌 처리 가능).
- **렌더 크기:** 캐릭터 픽셀아트는 기본 3×5px, 일부 캐릭터 4×5px. 높이 5px는 **그림의 상징적 키**이지 1.67m 실제 신장 계산값이 아니다.
- 픽셀 경계와 관계없이 좌표는 `(x_cm,y_cm)`로 관리. 렌더링할 때 nearest-neighbor 확대, subpixel anti-aliasing 사용하지 않음.
- 기본 렌더 프레임: `idle 2 / walk 4 / fire 2 / hit 1 / disabled 1` = 캐릭터당 10개 작은 프레임(초기에는 애니메이션 대신 1프레임으로 시작 가능).
- 적 발견 범위(시야), 공격 거리, 이동 속도는 **모두 meter 또는 m/s** 단위이며 동일 게임 좌표계 사용.

### E.2 전 보병 캐릭터 설정표

**아래 수치는 현실 성능이 아니라 게임 밸런스용 임의 설계값.** 1.0.0 릴리스에서 다섯 타입을 모두 지원하되, 각 타입은 순차적 사이클에서 구현한다.

| 타입 | ID | 스프라이트 | 1인 HP | 이동 속도 | 감지 반경 | 게임 공격 범위 | 공격 간격 | 추상 피해 | 구매 비용/인 | 주 역할 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 기본 보병 | `INF` | 3×5px | 100 | **1.6 m/s** | **36m** | 22m | 2.0s | 11 | 16 | 점령/경계/기본 방어 |
| 정찰 보병 | `REC` | 3×5px | 80 | **1.9 m/s** | **60m** | 18m | 2.5s | 7 | 25 | 발견·시야 제공, 경전투 |
| 지원 보병 | `SUP` | 4×5px | 110 | **1.3 m/s** | **32m** | 27m | 3.0s | 16 | 28 | 분대 방어, 공격 간격 길게 |
| 의무 보병 | `MED` | 3×5px | 80 | **1.6 m/s** | **30m** | **공격 없음** | — | — | 25 | 아군 치료, 거점 인원 유지 |
| 공병 보병 | `ENG` | 3×5px | 90 | **1.4 m/s** | **30m** | **공격 없음** | — | — | 25 | 장비/장애물·시설 작업 |

**추가 필드(전 타입):** `id`, `team`, `type_id`, `pos_x_cm`, `pos_y_cm`, `heading_0_7`, `hp`, `ammo`, `alive`, `squad_id`, `task_state`, `target_id`, `cooldown_ms`, `last_seen_enemy_ids`, `carrier_id?`. `MED`의 `healing_supply`, `ENG`의 `repair_supply`는 별도 필드. 수치 단위를 필드 이름 또는 타입 문서에 기록한다.

#### E.2.1 탄약/회복 초기값

| 유형 | 초기 ammo | 재장전/보급 용량 | 추가 자원 |
|---|---:|---:|---|
| INF | 30 | 30 | 없음 |
| REC | 20 | 20 | 없음 |
| SUP | 45 | 45 | 없음 |
| MED | 0 | 0 | `heal_pool=80` HP만큼 회복 가능, 병원/트럭에서 재보급 |
| ENG | 0 | 0 | `repair_pool=50` 추상 작업 포인트 |

탄약 1단위 = **한 번의 추상 공격 이벤트 시도**. 재장전은 공급 지점 또는 트럭 인접 시 4초(1인 기준) 걸린다. 총알별 충돌/탄도 모델은 생성하지 않는다.

### E.3 분대 편성(명령 단위)

| 편성 | 구성 | HQ가 다루는 개체 | 관전 표시 |
|---|---|---|---|
| `SQUAD_INF` | INF ×5 | 1 squad ID, 실제 Entity 5 | 멀리서 `●5`, 가까이서 5명 |
| `SQUAD_REC` | REC ×3 | 1 squad ID | `△3` |
| `SQUAD_SUP` | INF ×3 + SUP ×1 | 1 squad ID | `◆4` |
| `SQUAD_MED` | INF ×2 + MED ×1 | 1 squad ID | `✚3` |
| `SQUAD_ENG` | INF ×2 + ENG ×1 | 1 squad ID | `⬡3` |

편성 가격은 구성 인원의 **구매 비용 합**이며, 인원 티켓은 총 인원수만큼 차감한다. 유닛 1인마다 따로 HQ 정책을 호출하지 않는다. 분대 대형 좌표는 `leader position` 주변 최대 2m 간격의 간단한 2열 구조로 엔진이 자동 생성한다.

### E.4 이동 FSM — 보병

1. `IDLE`: 명령 대기. 마지막 유효한 HOLD/DEFEND 명령은 유지.
2. `ORDERED`: 소유권/좌표 확인.
3. `PATH_PENDING`: 4m grid A* 1회 계산, 결과 캐시.
4. `MOVING`: 매 0.2초 `distance = movement_speed × 0.2` 이하만 이동. squad 이동은 **느린 구성원 속도**를 기본으로 한다.
5. `BLOCKED`: 장애 발생 시 국소 우회 1회, 실패하면 명령 실패 이벤트. 매 tick 전체 길찾기 재호출 금지.
6. `ARRIVED`: 목표 반경 1.5m 내 도착. 다음 명령 단계 실행 또는 HOLD.
7. `INTERRUPTED`: 탑승·회복·비활성·취소·연료 문제 등의 이벤트로 안전하게 상태 전환.

#### 1초 이동 거리 예시(게임 수치)

- INF는 약 1.6m → 4.8 render px; 0.2s tick당 0.32m → 0.96 render px.
- REC는 약 1.9m → 5.7 render px; 0.2s당 0.38m → 1.14 render px.
- 픽셀아트 위치는 가까운 화면 픽셀로 반올림해 보이지만 **물리 좌표는 손실 없이 누적**하므로 대각선 이동에서도 속도가 달라지지 않음.

### E.5 적 감지·시야 규칙

- **시야 검사 주기: 1 simulated second**(각 보병 0.2초마다 전체 상대 검사 X).
- 병사 A와 대상 B의 거리 `d`가 `A.detection_radius_m` 이내일 때만 시야 검사를 진행한다.
- `WALL/BUILDING` 타입은 라인 캐스팅에서 시야를 차단. `FOREST`에 있는 관찰자의 감지 반경은 ×0.7, 목표가 숲 안에 있으면 추가 ×0.8(임의 게임값).
- 완전한 관측 정보는 해당 팀에게만 `visible_enemy_ids`로 전달. 마지막 발견 기록은 `last_seen_xy, seen_at_sim_s`와 함께 남기고, 60초가 지나면 삭제(설계값).
- 관측은 **위치가 알려졌다는 사실**일 뿐 자동 공격 명령이 아니다. 분대의 `DEFEND/HOLD` 내부 FSM이 적이 게임형 공격 거리 안에 들어온 경우에만 대응한다.
- 통신타워를 점령하면 **일부 지역의 감지 갱신을 20% 빠르게** 하거나 제한된 감지 반경 보너스를 준다. 적 전원 좌표를 볼 수 있게 하지는 않는다.

### E.6 공격 규칙(엔진 전용)

- 대상이 실제로 **현재 감지됐고**, 거리·쿨다운·ammo·행동상태·사선 조건이 맞으면 `ATTACK_EVENT`를 기록한다.
- 성공 여부는 엔진의 **seeded PRNG**로 결정한다. 시작 적중 확률: INF 0.55, REC 0.45, SUP 0.50(임의 게임값). `COVER` 효과 적용 시 ×0.8.
- 공격 성공: 해당 유형의 위 표 `추상 피해`만큼 HP 감소; 실패: HP 변화 없음. 어떤 경우에도 ammo 1 소모.
- **병사/차량의 현실적 손상 기전, 폭발 반경, 사격 궤적, 실제 무기 사거리·장갑 관통은 구현하지 않는다.**
- HP ≤0: 해당 캐릭터를 `DISABLED`로 바꾸고 점령 가중치를 잃음. 픽셀 애니메이션으로 짧게 회색 점멸 뒤 전장에서 비활성화. 의료병은 `hp >0`인 아군만 회복(실제 전장에서의 치료 모델이 아님).
- 이 게임의 **차량에는 무장·자동발사·공격 타깃 능력 X**. 차체는 1.0.0에서 이동/좌석/연료/지형만 모델링하여 운용 로직을 간소화한다.

### E.7 MED/ENG 게임 기능

- MED: 같은 편·반경 3m·환자가 HP(1..max-1) 범위·heal_pool>0일 때 2초마다 HP +8. 치료는 치료자/대상이 이동하면 중단. 병원에서 heal_pool 충전.
- ENG: 1.0에서는 **도로 작은 장애물 1개 해제(5초), 차량 경로 막힘 검사 1회 지원, 보급창 시설 상태 복구(10초)** 정도만 제공. 사실적 폭발물 처리/폭파·지뢰/시설 파괴는 미구현.
- 기능이 너무 많아지면 MED/ENG는 **구성 타입 정의만 먼저 생성**하고 실제 행동 구현을 C19 이후로 밀어둔다. 단, 타입 ID/스프라이트/속도/시야는 고정.

### E.8 레이어별 픽셀 표현

| 카메라 확대 | 병사 표기 | 분대 표기 | 성능 |
|---|---|---|---|
| 줌 0.25–0.75× | 개별 병사 렌더 생략 | ID·인원수 아이콘 1개 | 객체 수 절감 |
| 줌 1×–2× | 개별 3×5px 픽셀 보병 | 분대 테두리·최소 상태바 | 기본 관전 |
| 줌 4×–8× | 걷기·정지·공격 추상 애니메이션 | 유닛 선택/시야 반경 | 상세 관전 |

팀 A는 푸른색 계열, 팀 B는 붉은색 계열(접근성 설정에서 교체 가능), MED/ENG는 별도 소형 심볼. 외형 차이를 별도 스프라이트 이미지 파일로 만들더라도 엔진 데이터에 영향을 주지 않는다.

---

## F. 탈것 정확 사양 — **수송 전용 / 무장 없음**

### F.1 차량 객체의 최소 필드

```text
Vehicle {
  id, team, type, pos_x_cm, pos_y_cm, heading_0_7,
  footprint_w_cm, footprint_h_cm, speed_mps,
  fuel_current, fuel_max, fuel_cost_per_100m,
  passenger_ids[], passenger_capacity, cargo_supply,
  cargo_capacity, state, order_id, route[], arrival_radius_m
}
```

차량의 차체 게임 체력/기계 고장·무장 등은 **1.0.0에서 필수 필드가 아니다**. 차량 1개는 이동 FSM 1개. 보병 탑승 시 보병은 `ONBOARD` 상태가 되어 별도 물리 이동/감지/공격을 하지 않는다.

### F.2 차량 종류별 수치

| 타입 | ID | 렌더 픽셀 | 논리 발판(폭×길이) | 게임 속도 | 탑승 | 화물 공급 | 연료 최대 | 소비/100m | 비용 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 경수송차 | `LUV` | **15×9px** | 5×3m | **8.0m/s** | 4인 | 0 | 100 | 2 | 100 |
| 장갑수송차 | `APC` | **21×12px** | 7×4m | **5.5m/s** | 8인 | 0 | 100 | 3 | 180 |
| IFV(수송형) | `IFV` | **24×12px** | 8×4m | **5.0m/s** | 6인 | 0 | 100 | 3.5 | 230 |
| 수송 헬기 | `HEL` | **24×24px** | 8×8m | **11.0m/s** | 8인 | 0 | 100 | 6 | 220 |
| 보급차 | `TRK` | **21×12px** | 7×4m | **5.0m/s** | 0인 | 120 | 100 | 3 | 95 |

**실제 군용 차량 제원과 무관한 아케이드 수치**이며, IFV/APC도 총포·포탑·탄약 없음. IFV의 목적은 지형 성능 차별화: `GRASS`에서 IFV ×0.90, APC ×0.70, `ROAD`에서 둘 다 1.00. LUV는 ROAD ×1.0, GRASS ×0.65. HEL은 지형 이동 제한을 받지 않지만 착륙 제한. 차량 `cargo_supply`는 보병 탑승과 별도다.

### F.3 탑승 시퀀스 및 게임 엔진의 일

1. HQ → `EMBARK`(분대 ID, 차량 ID)를 명령 큐에 제출.
2. 엔진이 **동일 팀**, 차량 승차 가능, 충분한 빈 좌석, 주변 접근 경로를 검사.
3. 분대가 차량 반경 2m까지 자동 이동. 차량은 속도 0으로 대기.
4. 분대원이 순서대로 1인당 **0.5 sim seconds**에 탑승. `passenger_ids`에 추가하고 보병 `ONBOARD`로 설정.
5. HQ → `TRANSPORT`(차량 ID, 목적지 좌표) 명령. 엔진이 차량/헬기 이동 경로 계산.
6. 경로 주행 중 엔진이 **0.2초 tick마다 거리/연료/충돌/좌표** 갱신. HQ AI는 기다린다.
7. 도착 뒤 `DISEMBARK`. 엔진이 승객별로 차체 주변 충돌 없는 위치를 찾아 1인당 0.5초에 하차.
8. 지점이 막혀 있으면 최대 반경 8m에서 안전한 게임 타일 검색, 실패 시 `NO_DISEMBARK_SPACE` 이벤트.

### F.4 차량의 이동 FSM

`IDLE → WAITING_PASSENGERS → READY → PATHING → MOVING → ARRIVED → UNLOADING → IDLE`.

오류 상태: `NO_FUEL`, `BLOCKED`, `NO_PATH`, `CAPACITY_EXCEEDED`, `LANDING_INVALID`, `OUT_OF_BOUNDS`. 각 오류는 명령 버스 이벤트에 남기고 HQ가 **다음 30초 정책 tick에서만** 재계획. 오류가 났다고 LLM을 즉시 호출하지 않는다.

### F.5 지상 이동 경로

- A*는 4m navigation grid에서 수행. 차량 발판 폭을 포함해 지나갈 수 없는 좁은 통로를 미리 마스킹.
- 거리 `dx,dy`를 계산하고 매 tick `max_distance = speed × terrain_factor × 0.2`만큼 이동.
- 각 100m 누적 이동마다 fuel 감소. 나머지는 `distance_accumulator`에 저장해 소수점 누적 손실 방지.
- 차량이 다른 차량 때문에 막혔다면 작은 우회/대기 후 `BLOCKED` 상태. 충돌을 물리 폭발로 처리하지 않음.
- **차량끼리 충돌시 서로 겹치지 않도록 정지**시키며, 충돌 피해는 구현하지 않는다.

### F.6 헬기 단순화

- 맵에서 출발점과 목적지 사이 게임상 2D 직선/웨이포인트 이동. 3D 기울기·로터·바람·고도·공기저항 없음.
- 착륙 가능한 영역에 주기적으로 생성하는 `landing_footprint`만 검사; 기본 헬기 발판 8×8m, 이착륙 지점 10×10m 이상 장애물 없음.
- 이륙·착륙은 각 4초 고정 애니메이션/타이머. 이동 중 승하차 불가.
- 수송 헬기는 **공격, 위협 회피용 자동 작전, 포격, 폭탄, 정찰 전용 레이더 모두 없음**. 탑승·이동·하차만 제공.

### F.7 차량 최종 목적지 판정

- 도착 범위 `arrival_radius_m=2.0`(지상), `4.0`(헬기 착륙 지점).
- 목표 좌표는 지형 유효성 검사 후 차량의 실제 발판 크기로 충돌 검증.
- `MOVE`/`TRANSPORT`가 완료되면 `ORDER_COMPLETED` 이벤트와 실제 도착 좌표 기록.
- 차량 스프라이트의 방향은 `heading` 각도로 회전시키되 **픽셀아트 계단 현상**을 유지할 수 있도록 8방향 atlas 사용 권장.

### F.8 자원 최적화 요점

- 차량당 별도 AI 모델 없음.
- 이동 중 매 프레임/매 tick LLM 호출 없음.
- 이동 경로가 유지되면 A* 재계산 없음.
- 탑승 인원은 차량 좌표에 종속되므로 위치 시뮬레이션 비용 절감.
- 차량 그래픽과 물리 발판 데이터 분리. 브라우저가 차량 이미지를 그려도 엔진 스텝 비용은 영향 없음.

---

## G. 거점·자원·승리 규칙 — 구현 가능한 최소 상태

### G.1 경기 모드

기본 `CONQUEST`: Team A/Team B 모두 같은 수량의 병력/자원/맵 거리에서 시작. UI는 A 공격·B 방어로 표시할 수 있지만 실제로 두 팀 모두 점령 가능하며 **상대 정책 학습에 공정**하도록 대칭 배치한다. B가 특정 거점을 보유하는 진정한 비대칭 공성전 모드는 **v1.1.0 이후**로 보류.

### G.2 최초 1.0.0 승리 조건

- 통신타워/중앙광장/남부보급창 3개 거점.
- `INF, REC, SUP, MED, ENG` 모두 alive+도보 상태면 점령에 **1인당 1 가중치**. 차량에 탑승한 상태는 0.
- 적이 없는 상황에서 아군 최소 **3명**이 반경 안에 들어와 20초 유지하면 중립 거점 획득. 적 거점은 15초 중립화 후 20초 점령.
- 통제 거점 하나당 매 30초 +1점. Hot Zone으로 표시된 거점은 +1 추가, Hot Zone은 5분마다 회전.
- 100점 먼저 달성한 팀 승리. 최대 45분 시뮬레이션에서 점수가 높은 팀 승리. 동점이면 5분 연장 후 무승부 처리.
- 공격/상대 유닛 비활성화 자체는 승점이 아니라 **점령과 보급을 위한 간접 효과**. 목표는 적을 최대한 많이 비활성화하는 것이 아니라 거점을 운영하는 것.

### G.3 초기 팀 자원과 편성

| 자원 | A/B 동일 시작값 | 소모/증가 |
|---|---:|---|
| Credits | **1,000** | 보병·차량 신규 생성시 차감. 1.0에는 크레딧 자동 생성 없음 |
| Personnel tickets | **70명** | 인원 생성 시 차감. 인원이 비활성화되어도 즉시 환불 없음 |
| Team supply | **300** | 의무/공병/탄약·연료 보급. HQ +3/60초, South Depot 소유 시 +8/60초 |
| Active soldier cap | **40명** | 모든 보병 타입 합 |
| Active vehicle cap | **7대** | 모든 수송차량 합 |

초기 편성: `INF 분대 ×2(10명)`, `REC 분대 ×1(3명)`, `MED 분대 ×1(3명)`, `APC ×1`, `HEL ×1`, `TRK ×1`. **초기 배치 유닛에 비용을 차감할지 여부는 명확히**: 여기서는 비용/티켓을 차감하는 것으로 고정. 초기 구성 총 16인, tickets 54 남음. 금액은 E절 인원 단가 합 + 차량 F절 단가 합으로 계산하며, 경제 테스트에서 시작 예산 초과면 경기 시작 자체를 거부한다. `SUP`, `ENG`, `IFV`, `LUV`는 경기 중 구매 가능.

### G.4 보급의 1.0.0 최소 규칙

- 물자 가격 단위는 실제 비용이 아닌 게임 값. `ammo 10` 재보급은 팀 supply 2 소모, `HEAL 10HP`는 supply 1 소모, `fuel 10`은 supply 3 소모.
- HQ에 가까운 `SUPPLY_NODE`나 TRK 3m 반경에서만 보급 가능. TRK 물자는 팀 창고에서 출발할 때만 적재하며, 적재한 물자와 팀 재고가 동시에 남는 복제 버그 금지.
- `TRK`는 화물만, 보병 수송 안 함. HEL은 인원 수송만(화물 운송은 후속 버전).
- 팀 supply가 0이면 신규 탄약·연료·치료 불가. 기존 병력이 자동으로 사라지지 않음.

### G.5 필수 이벤트

`MATCH_STARTED`, `UNIT_SPAWNED`, `ORDER_ACCEPTED`, `ORDER_REJECTED`, `UNIT_MOVED`, `UNIT_ARRIVED`, `UNIT_SPOTTED`, `ABSTRACT_ATTACK`, `INFANTRY_DISABLED`, `EMBARK_STARTED`, `EMBARK_DONE`, `DISEMBARK_DONE`, `VEHICLE_OUT_OF_FUEL`, `CAPTURE_PROGRESS`, `OBJECTIVE_CAPTURED`, `SCORE_TICK`, `SUPPLY_CHANGED`, `MATCH_ENDED`.

로그는 **state truth**에서 발행되는 관측 가능한 이벤트이며, 개인별 UI 애니메이션 이벤트는 추가될 수 있지만 학습 상태를 변경하지 않는다.

---

## H. 구현 폴더 — 버전별 격리

**루트 규칙:** 이 릴리스 관련 모든 소스/실행 파일은 `v1.0.0/`에 둔다. 프로젝트 루트의 기존 자료는 건드리지 않는다. 향후 버전은 별도 `v1.1.0/` 또는 `v2.0.0/`를 만들고 필요한 모듈을 명시적으로 복제/이관한다. 버전 폴더를 자동으로 덮어쓰지 않는다.

```text
repo-root/
  README.md                     # 최상위 안내 (기존 내용 존중)
  v1.0.0/
    CODEX_EXECUTION_PLAN.md     # 이 문서 (Codex 실행 기준)
    STATE.md                    # 단 한 장 진행 현황 / 다음 사이클
    README.md                   # 구동/개발 안내 (C01에서 생성)
    pyproject.toml              # Python 패키징/테스트 최소 의존성
    .env.example                # 비밀값 없는 샘플
    config/
      game.yaml                 # 맵/기본 시간/점수
      units.yaml                # E절 보병 수치
      vehicles.yaml             # F절 수송차 수치
      logistics.yaml            # G절 자원 수치
    engine/
      __init__.py
      types.py                  # 엔티티/명령/게임 상태 타입
      state.py                  # GameState 및 순수 갱신
      rng.py                    # seed RNG
      map.py                    # 타일/시설/경로 그리드
      pathfinding.py            # A*
      orders.py                 # enum/검증/queue
      movement.py               # 모든 엔티티 물리 좌표 변경
      infantry.py               # 캐릭터 자동 행동 FSM
      transport.py              # 승하차 및 차량 FSM
      sensing.py                # 팀별 시야/발견 상태
      combat.py                 # 게임형 추상 피해 이벤트
      objectives.py             # 점령/점수/승리 판정
      logistics.py              # 구매·보급·치료
      events.py                 # append-only event serialization
    agents/
      rule_hq.py                # 코딩된 간단 HQ 전략
      model_hq.py               # 추후 정책 모델 어댑터
    learning/
      env.py                    # PettingZoo dual-agent wrapper
      train.py                  # 향후 RL 학습 엔트리
      evaluate.py               # 정책·seed별 평가
    viewer/
      package.json              # C24 이후
      src/
    server/
      app.py                    # C27 이후
    tests/
      test_state.py
      test_orders.py
      test_movement.py
      test_sensing.py
      test_transport.py
      test_objectives.py
      test_replay.py
    data/
      .gitkeep                  # 실제 실행 로그/가중치는 .gitignore로 제외
```

**주의:** 위 파일은 최종 목표 디렉터리 목록이지 C01에서 전부 빈 파일로 만드는 지시가 아니다. **각 Cxx에서 필요한 파일만 처음 생성**한다. 초반에는 `engine/`, `tests/`, `config/` 일부만 존재해야 한다.

### H.1 `STATE.md`의 고정 템플릿

```markdown
# DECEPTION CTRL v1.0.0 STATE

Current cycle: C01
Status: NOT_STARTED
Last completed: none
Last tests: not run
Known blockers: none
Next single task: create minimal package + config parser
Remaining Plus quota: UNKNOWN (check /status or Usage; never invent)
Notes: retain existing user changes
```

매 사이클 끝날 때 **10–15줄 안에** 상태 갱신. 장황한 일지는 `STATE.md`에 추가하지 않는다. 세부 테스트 로그는 필요 시 `data/logs/`의 별도 파일로 남기되 Git 커밋에 불필요한 대용량 로그 추가 금지.

### H.2 수정이 허용되는 경로

- 허용: 해당 `v1.0.0/`의 파일, 필요한 범위의 최상위 `.gitignore` (기존 줄 보존).
- 금지: 다른 버전 폴더, 사용자 개인 데이터, 다른 프로젝트 파일, 시스템 디렉터리, 코드에 들어갈 토큰/비밀값.
- 변경 전 `git diff --`로 기존 수정 확인, 관련 내용 충돌 시 임의 덮어쓰기 금지.

---

## I. 36개 소형 구현 사이클 — 정확한 작업 카드

**사용법:** `Cxx` 카드 한 개가 한 세션의 전부다. 한 날에 3개를 실행할 수 있으면 진도를 나가지만 실제 완료율·사용량에 따라 **한 Cxx가 여러 세션에 걸쳐도 정상**이다. 카드 이름/ID는 고정. DoD 미달이면 다음 카드 진행 금지.

### Phase 0 — 기초 구조(예시 Day 1: C01–C03)

#### C01. 프로젝트 최소 부트스트랩

- **입력:** 본 문서 H절 경로, `config/game.yaml` 최소 데이터(128×128m, 0.2s tick).
- **구현:** `v1.0.0/README.md`, 최소 `pyproject.toml`, config parser와 `pytest` 실행 가능 상태, `STATE.md`.
- **절대 제외:** 전체 디렉터리 미리 생성, LLM, 웹, 차량, 점령 로직.
- **DoD:** `python -m pytest`가 테스트 1개로 성공; 잘못된 지도 폭(0 또는 음수)을 거부.
- **회차 종료 보고:** 생성 파일과 설치 없이 실행 가능한지 여부.

#### C02. 기본 Entity 타입

- **구현:** `WorldPos`, `Soldier`, `Squad`, `Vehicle`, `Facility`, `TeamState`, `Command`의 타입/초기화/ID.
- **주의:** 실제 이동이나 전투 로직 구현 금지. `x_cm/y_cm`와 `team enum` 일관성만 확인.
- **DoD:** `Soldier` 생성·직렬화·불변량(팀, 좌표, 인원)이 단위 테스트 통과.

#### C03. RNG와 초기 WorldState

- **구현:** seed 수용, 지도 크기, 타이머, 두 팀, 2개의 테스트 보병, clone/checksum 가능한 상태.
- **DoD:** 동일 seed로 두 번 초기화하면 상태 해시 동일. seed가 다르면 맵 난수 객체 샘플이 달라짐.
- **범위 제외:** 렌더·점령·보급.

### Phase 1 — 순수 엔진(예시 Day 2: C04–C06)

#### C04. 유효 명령 검증

- **구현:** C.3 명령 JSON Schema/enum, 외부 좌표·적 부대 소유권·알 수 없는 op 코드 거부.
- **DoD:** 합법 `MOVE` 큐에 수락; `FOREIGN_UNIT`, `OUT_OF_BOUNDS`, `UNKNOWN_OP` 테스트.

#### C05. Queue와 인생주기

- **구현:** `command_id` 멱등 처리, TTL/priority, 완료/취소/오류 상태, `CommandEvent`.
- **DoD:** 동일 명령 두 번 수신해도 실행 1회. 취소된 명령은 움직이지 않음.

#### C06. 결정론적 `step(dt)`

- **구현:** 0.2s 고정 tick 루프, time accumulation, 명령 이벤트 수집; 최소 engine 경로.
- **DoD:** 입력과 seed가 같으면 1,000 tick 뒤 state hash 동일. 엔진 단독으로 네트워크/LLM 호출 없음.

### Phase 2 — 지도와 보병 이동(예시 Day 3: C07–C09)

#### C07. 128m 지형 데이터

- **구현:** D.4 타일코드(초기 0,1,3), 경계, 이동 가능성 계산, 테스트 시설 2개.
- **DoD:** out-of-bounds 시 예외/명령 거부. wall 통과 불가 테스트.

#### C08. 4m Grid A* 경로

- **구현:** 시작/도착, 비용, 장애물 마스크, 경로 캐시, unreachable 응답.
- **DoD:** 장애물 통과 안 함, 동일 지형에서 경로 재현, 경로 없으면 `PATH_NOT_FOUND`.

#### C09. INF 단일 보병 이동 FSM

- **구현:** 기본 INF가 `MOVE`를 받은 뒤 1.6m/s로 경로를 따라 이동. 엔진이 좌표 갱신.
- **DoD:** 10s 직선 자유 이동 최대 16m±허용오차, 경계 바깥 이동 없음, 명령 완료 이벤트 1회.
- **제외:** 다른 병종, 공격, 시야, 차량.

### Phase 3 — 캐릭터 시스템(예시 Day 4: C10–C12)

#### C10. E절 보병 데이터 설정 로딩

- **구현:** `INF/REC/SUP/MED/ENG`의 `config/units.yaml` 정형 수치와 스프라이트 메타데이터.
- **DoD:** 5개 타입 모두 `size, hp, speed, detection, attack` 범위 검사. 공격하지 않는 MED/ENG에서 공격 능력 없음.
- **제외:** 새 스프라이트 제작/애니메이션.

#### C11. 분대(최대 5인) 자동 추종

- **구현:** `Squad`가 명령을 받으면 구성 보병이 상대 위치를 유지하며 뒤따름. 병사별 HQ 호출 없음.
- **DoD:** 동일 그룹의 5인 이동, 중복 ID·전장 밖 위치 불가, 느린 멤버 속도로 그룹 속도 제한.

#### C12. 팀별 탐지/시야 엔진

- **구현:** 1s당 `distance + line-of-sight` 검사, 숲/벽 효과, 팀별 `visible/last_seen`.
- **DoD:** 벽 뒤 적 미탐지, REC가 INF보다 먼 테스트 적 발견, 상대 비공개 좌표 누출 없음.

### Phase 4 — 추상 전투와 거점(예시 Day 5: C13–C15)

#### C13. 보병 게임형 공격 이벤트

- **구현:** E.6의 사거리·쿨다운·ammo·게임형 확률/HP, `DISABLED` 상태.
- **DoD:** 같은 seed/명령열에서 피해 기록 동일; MED/ENG 공격 이벤트 0; ammo가 0이면 공격 불가.
- **제외:** 실제 탄도·총기 제원, 차량 공격.

#### C14. 점령 게이지

- **구현:** 중립/팀 소유/경합, 최소 3인, 20초 획득/15초 중립화, 탑승 인원 미반영.
- **DoD:** 적 없이 3인 도착하면 점령 완료, 2인은 점령 불가, 양팀 동수면 멈춤.

#### C15. 점수/승리·연장

- **구현:** 30초 +1, Hot Zone +1, 100점 승리, 45분 제한, 동점 시 5분.
- **DoD:** 선취 100점 테스트, 끝에서 1초/0.2초 경계 오차 없이 처리, 동점/연장/무승부 모두 테스트.
- **필수 출력:** `headless_match_summary.json` 샘플 1개(작은 128m 시나리오).

### Phase 5 — 탈것/수송(예시 Day 6: C16–C18)

#### C16. 차량 종류와 이동 엔진

- **구현:** F절 `LUV/APC/IFV/HEL/TRK`의 픽셀 크기/발판/속도/연료/탑승능력 설정, 지상차량 1대 경로 이동.
- **DoD:** 지형별 속도 및 100m당 연료 감소 확인, 0 연료 이동 중단, 무장/공격 메서드 없음.
- **제외:** 승하차, 헬기 이착륙.

#### C17. 보병 승차 FSM

- **구현:** 차량 정차/반경 2m/빈 좌석 검사, 0.5s/인, `ONBOARD` 및 manifest 일관성.
- **DoD:** 8인 APC에 9명 탑승 거부, 타 팀 차량 탑승 거부, 탑승 중 보병 좌표 분리 갱신 없음.

#### C18. 하차·헬기 수송

- **구현:** 하차 안전셀 검색, HEL 직선/웨이포인트 운행과 4초 이착륙 타이머, landing 검증.
- **DoD:** `EMBARK → TRANSPORT → DISEMBARK` 1회 전체 end-to-end, 탑승 인원 중복/좌표 이탈 없음.
- **제외:** 헬기 실물 비행물리·무장/조준.

### Phase 6 — 보급과 2 HQ(예시 Day 7: C19–C21)

#### C19. 보급/치료 최소 기능

- **구현:** `TeamState` 자원 원자 차감, 분대 ammo, MED 치료, TRK 재고 적재/하역, HQ/South Depot 공급 증가.
- **DoD:** 팀 재고 음수/복제 없음, 치료량 상한, 공급 부족 시 명령 거부.
- **주의:** ENG의 복잡한 설치 작업은 같은 사이클에 넣지 말고 별도 다음 회차/이후 버전으로 미룰 수 있다.

#### C20. 규칙 기반 HQ v0

- **구현:** AI가 아니라 작은 결정 함수 `RuleHQ.observe_and_issue(obs)`가 30 sim seconds마다 최대 4개 합법 명령 반환.
- **기본 행동:** 가까운 비점령 거점 이동, 목표 도착 시 CAPTURE, 탄약/연료 부족이면 RESUPPLY, 나머지 HOLD.
- **DoD:** AI 없이 **게임 완주 10회**. HQ가 직접 좌표를 업데이트하는 코드가 없음.

#### C21. 팀 A/B 분리와 격리 테스트

- **구현:** `RuleHQ_A`와 `RuleHQ_B` 각각 관측/명령 큐 분리, 색상/시작 HQ 반사 대칭.
- **DoD:** A가 B의 비공개 병력 위치를 받지 않음. 10개 seed를 A/B swap해 실행하고 점수 기록.

### Phase 7 — 리플레이와 성능(예시 Day 8: C22–C24)

#### C22. 이벤트 리플레이 최소 기능

- **구현:** append-only `event_id, sim_tick, event_kind, payload`, checkpoint snapshot 저장/재적용.
- **DoD:** 동일 게임을 event/replay로 재생했을 때 최종 상태 checksum이 원본과 같음.
- **주의:** 전체 픽셀/모든 유닛 매 프레임 업로드 X.

#### C23. 1,024m 실험 맵 및 부하 측정

- **구현:** D.3 시설 좌표 + seed 대칭 지도 + 128m chunk, headless 벤치마크.
- **DoD:** 100/300/500개 엔티티별 `ticks_per_second, max_rss_mb, match_wall_time_s`, seed 교환시 이동거리 차이 기록.
- **성능 불합격:** 임계치 충족 못하면 웹/LLM 작업 중단하고 실제 프로파일러로 엔진 최적화.

#### C24. PixiJS 정적 픽셀 렌더

- **구현:** `viewer/` 기본 Vite+PixiJS 페이지, 지도 tile chunk, 카메라 pan/zoom, A/B 정적 부대·시설 배치.
- **DoD:** 3,072px 전체 맵 중 viewport만 렌더, 1×줌에서 캐릭터 3×5px·APC 21×12px 확인.
- **제외:** 웹 로그인·Supabase·실시간 서버.

### Phase 8 — 관전자와 API(예시 Day 9: C25–C27)

#### C25. 리플레이 위치·애니메이션

- **구현:** 기존 event/snapshot을 이용해 순서·시간대로 위치 보간, `0.5/1/2/4×` 재생.
- **DoD:** 같은 replay로 최종 부대 좌표/거점 점수가 일치하고, viewer 접속이 시뮬레이션 결과에 영향을 주지 않음.

#### C26. HQ 명령 패널·스코어 HUD

- **구현:** 현재 점수·시간·거점 진행도·소유 팀·수송 상태·HQ 최근 10개 명령 UI.
- **DoD:** 조작 불가능한 읽기 전용 UI, A/B 명령 순서·상태가 엔진 이벤트와 일치.

#### C27. 로컬 FastAPI 읽기 엔드포인트

- **구현:** `GET /matches`, `GET /matches/{id}`, `GET /events`, `GET /snapshot` 로컬 API.
- **DoD:** replay를 browser가 읽어 렌더, 쓰기/임의 코드 실행 API 없음.
- **제외:** 외부 공개/도메인/Oracle 배포.

### Phase 9 — 클라우드 관전(예시 Day 10: C28–C30)

#### C28. Supabase 경기 메타DB/RLS

- **구현:** match ID/승패/시작시각/점수/정책 버전/리플레이 URI 메타데이터, 공개 읽기 RLS와 관리자 쓰기 권한.
- **DoD:** 로그인 없는 공개 관전자는 공개 게임만 읽고, 관리자 테이블·비밀 키 읽기 실패 테스트.
- **승인 경계:** Supabase 프로젝트/환경변수 설정은 사용자가 권한을 제공한 후 수행.

#### C29. R2 업로드와 재생

- **구현:** 압축 replay를 로컬에서 생성하고 종료 후 R2 객체 1개 업로드, checksum 검증, 실패 시 retry queue.
- **DoD:** 정상 1개 업로드 및 브라우저 다운로드, 업로드 실패해도 원본 로컬 보존.
- **금지:** 매 0.2s frame 전송, 모델 weight 공개 버킷 업로드.

#### C30. Cloudflare Pages 읽기 전용 관전 공개

- **구현:** 빌드된 viewer를 Cloudflare Pages에 배포, Supabase 최근 결과 + R2 재생 데이터 연결.
- **DoD:** 외부 브라우저에서 최근 경기 승패/리플레이 확인, Mac 꺼져도 기존 경기 조회.
- **안전:** 배포는 사용자의 계정/대상/공개 범위 확인 뒤 수행. 첫 테스트는 비공개 우선.

### Phase 10 — RL 기준선(예시 Day 11: C31–C33)

#### C31. PettingZoo 2-agent Adapter

- **구현:** `reset(seed)`·`step({A:action,B:action})`, 관측/보상/종료 dict. 단순 고정 크기 벡터/마스크.
- **DoD:** 100 step 양팀 실행, shape 일관성, 적 비공개 정보가 자기 관측에 없음.

#### C32. 행동 공간 축소 + Random/Heuristic 기준선

- **구현:** `goal∈{N,C,S,RESUPPLY,HOLD}`, `squad_id`, `vehicle_id` 같은 소형 이산 선택, 무효 행동 mask.
- **DoD:** Random 정책/규칙 정책으로 각각 50개 seed 기록. 잘못된 선택으로 엔진이 crash하지 않음.

#### C33. 소형 정책망과 PPO 첫 훈련

- **구현:** 관측 벡터 → masked discrete action 분류에 맞춘 **작은 MLP**. 한 에이전트만 업데이트, 상대는 고정.
- **DoD:** 체크포인트를 저장/로드해 같은 입력에 동일 정책 출력, 100개 seed 평가를 기존 기준선과 비교.
- **주의:** 아직 로컬 SLM 호출하지 않음. PPO 라이브러리/SB3 wrappers의 최신 API는 설치 시 확인.

### Phase 11 — Self-Play와 로컬 SLM(예시 Day 12: C34–C36)

#### C34. 정책 풀 순차 Self-Play

- **구현:** A 동결·B 학습 → B 동결·A 학습, 과거 정책 보존, holdout seed 고정.
- **DoD:** 정책 3개 이상 버전 저장, 상대 정책마다 승률 표/경기 ID 기록. 개선 없으면 best 정책 유지.

#### C35. 객관적 평가 보고서

- **구현:** 승률·무승부·평균 점수차·유닛 손실·보급 사용·무효 명령·성능/seed별 비교를 Markdown/CSV로 요약.
- **DoD:** `rules vs PPO`, `old vs new`를 같은 seed 조건에서 대조, 학습 테스트 데이터와 holdout 분리 확인.

#### C36. 선택적 Qwen3.5/Gemma HQ 보조

- **구현:** 실제 Mac mini에서 Qwen3.5-0.8B와 Qwen3.5-2B(선택 Gemma 4 E2B) 중 **한 번에 하나**의 GGUF 모델 벤치마크. `STATE SUMMARY → JSON strategy hint`만 반환.
- **DoD:** 50개 상태에 대해 JSON 유효율, P50/P95 응답 지연, RSS, tokens/s 측정. `max 0–2 calls/match` 조건으로 AI HQ 보조. 실패하면 PPO/규칙 HQ로 자동 복구.
- **중요:** SLM이 물체를 이동하는 코드 작성 금지. 차량/병사별 모델 미생성. LLM fine-tuning/LoRA는 **v1.0.0 완료 조건 아님**.

### I.1 사이클별 작업량 조정 규칙

- Cxx가 예상보다 크면 `C16a/C16b`처럼 **하위 작업 카드 2개로 분해**하고 STATE에 기록. 필수 행동/DoD는 그대로 유지.
- 구현 중 추가 아이디어가 생기면 `BACKLOG`에 1줄만 기록하고 그 자리에서 구현하지 않는다.
- 조건문·타입 변경 때문에 테스트가 깨지면 **실패한 그 테스트부터 해결**. 다음 UI 기능 구현 금지.
- C36 이전에도 시뮬레이션은 **AI 없는 규칙 HQ로 항상 정상 실행**돼야 한다. LLM API 설치/모델 다운로드는 C36 전 금지.

---

## J. 리소스 최적화 구현 체크리스트

### J.1 AI 추론 비용을 줄이는 구조

| 흔한 고비용 방식 | 이 프로젝트에서 채택할 방법 | 효과 |
|---|---|---|
| 병사 1명마다 AI 모델 호출 | **분대 1개를 HQ 명령 대상**으로, 병사는 FSM | 모델 호출 수가 병사 수에 비례하지 않음 |
| 차량 이동 좌표를 LLM이 매 tick 계산 | **엔진이 `speed × dt` + 경로 점수** 적용 | 단순 이동에서 추론 불필요 |
| 적 감지 때마다 LLM으로 상황 질문 | 엔진이 LOS/반경을 계산하고 30s마다 HQ 요약 | 요청의 입력 토큰 절감 |
| 매 상태 전체 맵 100만 셀을 AI에 전달 | 최대 32~128개 객체 요약, 거점 3개 상태 | 프롬프트/관측 차원 감소 |
| 공격·점령/보급을 AI가 자유서술로 실행 | **검증된 0–12 opcode**만 선택 | 파싱/환각·실행 오류 감소 |
| RL을 LLM 전체 가중치 업데이트로 시작 | 작은 MLP PPO, LLM은 0–2회 전략 보조 | Intel CPU에서도 학습 가능성 증가 |
| LLM 생성 후 사후 예외 처리 반복 | 명령 action mask + strict schema + 규칙 fallback | 무효 명령 재시도 감소 |

### J.2 Game engine 최적화

1. `headless`는 Viewer/HTTP/DB 객체를 만들지 않는다. 경기 상태만 RAM에 유지.
2. `Fixed timestep=200ms`, 엔진 내부에서 network I/O block 금지.
3. 감지는 1s 주기. 먼저 4m/8m 셀별 공간 인덱스로 주변 후보만 조회, 그다음 거리/LOS.
4. 경로탐색은 **명령 수락 시 1회**, 길이 막힐 때만 다시. 전 부대를 매 tick A* 실행 금지.
5. 보병 그룹은 squad 단위 목표 경로를 공유하고 멤버는 각자 로컬 대형 좌표만 보정한다.
6. 승객 `ONBOARD`는 운송수단에 종속돼 별도 속도/시야 계산을 중단한다.
7. `order_id, unit_id, facility_id`는 정수로 유지하고 자주 읽는 상태는 간단한 객체/배열로 저장. 초기부터 과도한 ECS 프레임워크 도입하지 않음.
8. 훈련에서는 그래픽 생성·개별 이동 이벤트 고빈도 쓰기·cloud upload를 중지한다. 디버깅 경기에서만 상세 이벤트/렌더 활성화.
9. `event_writer`는 append-only 로컬 버퍼를 사용, 60s sim마다 snapshot, 경기 종료 시 압축/검증.
10. Python profiler로 실제 병목이 확인되기 전 Rust/C++ 재작성 금지. 고비용 hotspot만 후속 최적화.

### J.3 픽셀 렌더 최적화

1. 카메라에 보이는 128m 청크만 텍스처 로드·렌더.
2. `zoom < 0.75`일 때 개별 병사를 그리지 않고 squad marker로 LOD 전환.
3. 자주 바뀌지 않는 건물/도로는 `tile chunk texture`로 캐시, 유닛은 별도 sprite layer.
4. 프레임 애니메이션은 8방향 작은 spritesheet atlas를 공유. 같은 타입마다 새 텍스처 생성 금지.
5. 30fps를 최저 목표로 하고, 장면 복잡도에 따라 particle/FoW 애니메이션을 단계적으로 하향.
6. **PixiJS는 진짜 물리 상태를 계산하지 않는다.** `snapshot/event`를 읽고 보간하기만 한다.

### J.4 클라우드 비용 최적화

- `Supabase`: 1경기당 매치 메타 1~3행, 점수 변화/상태 요약 정도만 주기적 갱신. 매 병사의 좌표를 DB에 고빈도 저장 금지.
- `R2`: 경기 종료 후 압축된 event log와 snapshot만 업로드. 수십 GB 원시 픽셀 스트림 보관 금지.
- `Cloudflare`: 정적 관전 페이지 우선. 실시간 상태는 전송 속도 낮추고 브라우저에서 보간.
- `Oracle`: MVP 필수 아님. 공식 2026 Always Free 용량이 상시 2 OCPU/12GB 상당으로 표시되므로, 대규모 모델 학습/병렬 시뮬레이션 서버로 가정하지 않음.[O4]
- `Mac`: 인터넷이 끊겨도 headless 시뮬레이터가 계속 작동, 재연결 때 `uploader`가 누락된 결과만 멱등 업로드.

### J.5 실제 계산량과 목표(측정 전 가정 금지)

45분 게임의 0.2s tick은 `2,700/0.2=13,500 ticks`. 30s HQ policy decision은 `2,700/30=90/team`. 이것은 **기획상 확정 계산**이다.

처리량 목표는 별도로 정한다:

| 벤치 항목 | 초기 목표(제안) | 실패 시 첫 대처 |
|---|---|---|
| 128m, 20 병사, headless | 2000 tick/s 이상 *목표* | Python profiler 및 이벤트 빈도 점검 |
| 1024m, 100 병사, 10 차량 | 200 tick/s 이상 *목표* | 공간 인덱스/이벤트 빈도/경로 캐시 |
| 시야 검색 | 주변 유닛만 후보, O(N²) 전체 스캔 회피 | 4~8m spatial hash |
| 로컬 모델 HQ 요약 | 50 상태에서 P50/P95 기록 | 0.8B, 짧은 프롬프트, thinking off |
| 웹 500 스프라이트 | 목표 30 FPS 이상 | LOD와 보이는 chunk만 렌더 |
| 압축 replay 1경기 | 평균 0.5~2 MB *가정* | 이동 이벤트 간격 조절 |

위 tick/s와 리플레이 용량은 **목표/가정이지 Mac mini 실측 수치가 아니다.** 미달했다고 게임이 불가능한 것은 아니며, 다음 단계에 들어가기 전에 상한/체감 속도를 조정한다.

---

## K. 1.0.0 QA와 발행 기준

### K.1 정확성·안전 체크리스트

- [ ] 모든 소스·설정·asset·training script가 `v1.0.0/` 아래에 존재. 다른 버전 변경 없음.
- [ ] A/B HQ Policy는 **읽기 전용 관측 → 정형 명령**만 반환. 이동 좌표 변경 코드는 엔진에만 존재.
- [ ] 각 보병 타입 5개의 HP/속도/감지 반경/공격 여부가 `units.yaml`과 정확히 일치.
- [ ] 차량 5개 타입의 픽셀 크기, 발판, m/s, 승객, 연료, 비용이 `vehicles.yaml`과 정확히 일치.
- [ ] 차량 클래스와 opcode에 무장/공격/발사 관련 행동이 없다.
- [ ] 보병에게 `CAPTURE` 명령을 내리면 AI 추가 호출 없이 자체 이동·점령을 완료.
- [ ] 보병 5명을 APC에 태우고 다른 좌표로 이동, 하차시 각 위치가 유효.
- [ ] 같은 게임 seed·설정·명령을 재생하면 마지막 state checksum 일치.
- [ ] 한 팀의 관측에 상대가 발견되지 않은 유닛 ID/좌표가 절대 포함되지 않는다.
- [ ] 같은 seed·팀 교환 조건에서 map fairness와 score bias를 기록.
- [ ] 100점 승리, 45분 종료, 연장, 무승부, 자원 부족 예외 테스트 통과.
- [ ] Random / Rules / Learned 정책을 동일한 holdout seed로 비교할 수 있다.
- [ ] Mac 로컬 headless 경기만으로 완주 가능, 클라우드 장애 시 게임 정상 진행.
- [ ] 관전 UI가 실제 게임 상태를 수정하지 않는다.
- [ ] 브라우저에 비밀키/개인 정책 가중치/숨겨진 라이브 팀 관측 노출 없음.
- [ ] 자동 3회/일 실행은 명시적으로 설정되기 전까지 **없음**. 문서상 cadence일 뿐.

### K.2 테스트별 설계

| 테스트 | 예상 입력 | 기대 결과 |
|---|---|---|
| `test_move_distance` | INF 10s 직선 `MOVE` | 최대 16m 이동(장애 없을 때) |
| `test_detection` | INF 40m vs REC 40m | INF 미탐지, REC 탐지(벽·숲 없음) |
| `test_wall_occlusion` | 정면 10m, 중간 WALL | 서로 감지되지 않음 |
| `test_attack_exclusions` | MED/ENG가 가까운 적을 발견 | 공격 이벤트 없음 |
| `test_ammo_exhaustion` | INF ammo=0 | 공격 시도/피해 없음 |
| `test_transport_capacity` | APC에 9명 탑승 명령 | `NO_CAPACITY`, 기존 8명과 좌표 불변 |
| `test_vehicle_fuel` | APC fuel=0, 목적지 먼 곳 | `NO_FUEL`, 좌표 불변 |
| `test_heli_pad` | 8×8 HEL, 좁은 착륙 공간 | `LANDING_INVALID` |
| `test_hidden_state` | A 시야 밖 B 유닛 | A observation에 좌표 누출 없음 |
| `test_capture` | 중립 구역 INF 3명 20초 | A 점령 완료 이벤트 1개 |
| `test_30s_score` | A 거점 1개 통제 | 30s마다 +1점 |
| `test_replay_hash` | 동일 seed + 명령열 | state SHA-256 동일 |
| `test_cloud_outage` | 업로더 실패/재시도 | 로컬 경기 지속, 중복 match 행 없음 |

### K.3 상태 보고 형식(모든 Codex 세션 동일)

```markdown
Cycle: C09 — INF movement FSM
Status: PASS / PARTIAL / BLOCKED / BUDGET_STOP
Changed: [specific paths, max 3 implementation files]
Verified: pytest tests/test_movement.py — 8 passed
Performance: (only if measured) ...
Known limitations: ...
Next: C10
Quota: measured remaining XX% / UNKNOWN
```

불필요한 코드 전체 붙여넣기, 대용량 빌드 로그, 이전 Master Plan 전문을 결과 메시지에 다시 복제하지 않는다.

---

## L. 모델 선택과 점진적 AI 수준 상승

### L.1 v1.0.0의 세 수준

| 수준 | HQ 구현 | CPU 비용 | 도입 단계 |
|---|---|---|---|
| **L0** | `RuleHQ`: Python 코드가 관측 → 행동 enum 선택 | 아주 낮음 | C20 즉시 |
| **L1** | `PPOHQ`: MLP가 행동 확률 출력 | 낮음/중간 | C33 이후 |
| **L2** | `SLM Adviser`: Qwen3.5/Gemma가 전략 목표만 제안 | 중간~높음, 호출 빈도 극소 | C36 선택 |

L2에서도 **유닛 움직임은 게임 엔진**이며 LLM은 `priority_objective=N`, `posture=DEFEND`, `needs_supply=true` 같은 소규모 전략 변수만 반환한다. 직접 실행 명령을 생성해야 한다면 **허용 op 코드로 정규화하는 adapter**를 거친다.

### L.2 Intel Mac mini 첫 후보

1. **Qwen3.5-0.8B**: 가장 먼저 동작/추론 속도/구조화 출력 시험.[M1]
2. **Qwen3.5-2B**: 0.8B 품질이 불충분할 때 비교.[M2]
3. **Gemma 4 E2B**: 추가 비교군. 공식 Q4_0 로드 추정 2.9GB, KV Cache/추가 추론 자원은 별도.[M3]

`llama.cpp` 또는 검증된 로컬 GGUF 서버 사용, `max_output_tokens=64~128`, 짧은 1~4K 컨텍스트, 구조화된 JSON 출력, 모델 fallback. **모델 성능이나 토큰/s를 측정 전에 단정하지 않는다.** LLM LoRA/RLHF는 1.0.0 구현 필수 조건이 아니다.

### L.3 Self-Play가 실제로 학습하는 것

- 정책망이 `observation`을 보고 `CAPTURE/HOLD/RESUPPLY/TRANSPORT` 등 **명령 선택 성능**을 개선.
- 로컬 LLM이 원한다면 일부 전략 요약을 제공하고 정책이 참고. 하지만 강화학습 파라미터 업데이트는 별도 train loop에서 수행.
- `game_n → (명령, 결과, reward, 상대 정책 버전) 저장 → PPO 업데이트 → holdout 평가 → game_n+1`.
- A와 B의 학습 데이터를 구별하고 서로의 숨겨진 관측정보를 공유하지 않는다.
- 과거 정책 3개 이상과 고정 Rules/Random 상대를 평가해 상대 하나에게만 과적합되지 않는지 검사.

---

## M. 사용자 확인이 필요한 사항과 기본 가정

요청에 따라 사소한 사항 때문에 구현을 멈추지 않도록 아래 **기본값**을 확정했지만, 사용자 판단이 다른 부분은 v1.0.0 사양 고정 전에 수정하면 된다.

| 결정 항목 | 이 문서의 기본값 | 바꾸면 생기는 영향 |
|---|---|---|
| Plus 사이클 시각 | KST 08:00/14:00/20:00, 자동 예약 아님 | 실제 일일 루틴과 맞추면 됨 |
| '90% 토큰' | **표시되는 Plus 사용 가능량 기준 90% 상한, 10% 예비** | 고정 토큰량 또는 자동 계측을 보장할 수 없음 |
| 1.0.0 전장 | 1,024×1,024m | 실제 행정구 규모를 원하면 다중 청크/LOD 확대 필요 |
| 병사 캐릭터 | INF/REC/SUP/MED/ENG, 1인 1 Entity | 스프라이트/게임 속도/시야 설정 수정 필요 |
| 차량 전투 | **전부 공격 불가, 수송만** | 무장 추가는 밸런스/엔진 규모 확대이므로 v1.1 이후 |
| A 공격/B 방어 | 같은 조건에서 거점 점수 경쟁 | B 초기 방어거점을 가진 비대칭 모드는 별도 룰셋 |
| IPC 명칭 | 의미 미확인, 차량 타입에서 제외 | 실제 의미 확인 후 새 타입 만들기 |
| 로컬 LLM | 필수 아닌 선택적 HQ 전략 보조 | 순수 LLM 게임을 원하면 시간/발열/추론 횟수 재설계 필요 |

---

## N. 참고한 공식 문서와 근거 범위

| 출처 | 이 문서에 반영한 사실 |
|---|---|
| [O1: OpenAI ChatGPT Work/Codex Pricing](https://learn.chatgpt.com/docs/pricing) | Plus의 Codex 포함 및 사용량 공유, 현재 사용 현황 확인. 일정한 개인 토큰 한도 숫자는 문서로 보장되지 않음 |
| [O2: OpenAI Accounts & Sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions) | ChatGPT Plus의 5시간 사용량 창은 ChatGPT 플랜을 쓰는 앱에 공유됨 |
| [O3: OpenAI Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex) | 좁은 완료 조건과 검증 가능한 task contract, budget stop·resume 제안 참고 |
| [O4: Oracle Always Free](https://docs.oracle.com/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) | 2026년 공식 Ampere A1 Always Free 총량 1,500 OCPU h/9,000 GB h, 2 OCPU·12GB 상당 |
| [M1: Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) | 모델 존재·규모·설정 가능성 |
| [M2: Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) | 더 큰 로컬 비교 모델 |
| [M3: Google Gemma 4](https://ai.google.dev/gemma/docs/core) | E2B 추론 메모리 개요 |
| [E1: PettingZoo Parallel API](https://pettingzoo.farama.org/api/parallel/) | 두 에이전트의 동시 행동/부분 관측 게임 환경 설계 가능 |
| [E2: PixiJS](https://pixijs.com/8.x/) | 2D 웹 렌더 분리 설계 |
| [E3: WARDOGS 공식](https://www.team17.com/games/wardogs) | 거점 점수/보급/수송의 게임성에서 영감. 픽셀 RTS의 게임 규칙은 자체 제안 |
| [E4: Supabase Broadcast](https://supabase.com/docs/guides/realtime/broadcast) | 실시간 진행상황 전달, DB/RLS와 구분 |
| [E5: Cloudflare R2](https://developers.cloudflare.com/r2/pricing/) | 완성된 리플레이 객체 보관과 가격/무료한도 |

**근거 분리:** 공식 문서는 각 플랫폼/모델/게임의 존재 및 지원 기능만 검증한다. INF 속도 1.6m/s, 헬기 24×24px, 30초 HQ 주기, 구현 36사이클, 자원/점령 수치는 **DECEPTION CTRL의 임의 게임 설계값**이며 외부에서 검증한 실제 작전 수치가 아니다.

---

## O. 최종 개발 원칙 요약

1. **AI에게 결정만 시키고, 게임 엔진에게 움직임을 시킨다.**
2. **차량은 운송용**. 보병 캐릭터 다섯 종류의 속도·크기·감지·추상 공격을 명확하게 관리.
3. **Plus 90% 이하, 하루 최대 3번, 1세션 1작업**. 사용량 확인 불가 시 무리한 수치 추정 금지.
4. **모든 버전 파일은 v1.0.0 아래**. 이전 자료/다음 버전과 섞지 않음.
5. **코드가 작더라도 반드시 테스트**. 실시간 관전보다 먼저 헤드리스 결정론적 엔진·리플레이를 완성.
6. **SLM은 마지막 단계의 선택 기능**. Pure RuleHQ와 소형 RL 정책망만으로 게임이 완주되는 것이 1.0.0의 핵심.
7. **프롬프트는 작게, 기록은 구조적으로, 한도 부족하면 중단.** 다음 회차는 STATE만 읽고 이어서 진행.
