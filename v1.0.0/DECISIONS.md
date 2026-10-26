# MW-NV v1.0.0 — 확정 결정

2026-10-24 KST 사용자가 승인한 구현 계획. 원본 첨부는 참고 명세이며,
아래 결정은 원본의 상충하는 프로젝트명·선택적 LLM·실행 방식보다 우선한다.

## 제품과 운영

- 제품명 MW-NV. 원본의 DECEPTION CTRL은 이전 설계명이다.
- C01–C36 전체 로드맵을 유지한다. 한 번의 요청에서 한 Cxx만 진행한다.
- 우선 대상: Intel Mac mini 2018, RAM 32GB. GitHub clone 후 로컬 실행을 제공한다.
- 추가 과금 없는 기본 경로. 상용 LLM API·유료 GPU·자동 결제·자동 일정은 사용하지 않는다.
- 클라우드 관전은 로컬 실행의 필수 의존성이 아니다. C28–C30 연동은 유지하되
  실제 배포는 무료 조건과 계정 권한 확인 후에만 한다.
- `dev/v1.0.0`에 각 Cxx 완료 커밋을 push한다. 주요 단계에서 PR을 만들며,
  토큰/세션 중단 시 WIP와 짧은 상태 파일로 재개한다. 강제 push는 하지 않는다.
- 다음 세션은 STATE·이 문서·원본 A절·해당 작업 카드만 읽는다.
- 실제 사용량을 확인할 수 없으면 UNKNOWN. 90% 사용량 달성을 추정하지 않는다.

## HQ와 모델: 원본 C/L/C36 변경

- 로컬 LLM은 선택적 조언이 아니라 양팀 HQ 명령 생성의 필수 연동이다.
- `llama.cpp`의 `llama-server` 한 프로세스·모델 하나를 공유하고 A/B 관측은 격리한다.
- 엔진 0.2초 tick, HQ 30초 시뮬레이션 간격을 유지한다. 양팀 명령 수집 중 게임 시간을 멈춘다.
- 팀 처리 순서와 명령 적용 tick을 고정한다. JSON 명령을 엔진이 재검증한다.
- 시간 초과·형식 오류·무효 명령은 기록하고 해당 결정을 규칙 HQ로 대체한다.
- 결정론은 동일 seed·설정·기록된 명령열 기준이다. LLM의 재생성 일치는 보장하지 않는다.
- 실제 적용 명령·모델 설정을 리플레이에 기록한다. 모델 서버가 엔진 상태를 직접 바꾸지 않는다.
- Qwen3.5-0.8B가 첫 모델 후보. 도입 단계에서 GGUF 출처·라이선스·체크섬을 검증·고정한다.
- 모델은 Git에 넣지 않는다. 내려받기·서버 시작·게임 실행 절차를 제공한다.
- Intel Mac 검증과 Linux 클라우드 검증을 구분한다. 실측 전 성능을 주장하지 않는다.

## 추가 카드와 의존성 도입

- C01–C19: PyYAML + pytest로 엔진 기반 구현. C20 규칙 HQ, C21 팀별 격리.
- C21-L1: 명령/관측 계약을 사용하는 로컬 서버 어댑터, JSON 검증·timeout·fallback 테스트.
- C21-L2: 양팀 LLM 결정 수집과 게임 시간 정지/재개, 모델 준비 절차 및 실제 연동 검증.
  두 카드는 각각 한 회차이며 C21 이후, C22 이전에 수행한다.
- C22–C27: 리플레이·성능 측정 후 PixiJS/Vite 관전과 FastAPI 읽기 API.
- C28–C30: Supabase·R2·Pages 연동. C31–C35: PettingZoo·MaskablePPO·평가.
- C36: 선택 기능이 아니라 Intel Mac에서 LLM HQ 통합·성능·실패 복구 최종 검증.
- 최신 PyTorch의 Intel Mac 패키지 제약 때문에 PPO 학습은 기존 개발 환경의 CPU에서
  제한된 규모로 수행한다. 외부 유료 자원을 만들거나 장시간 학습을 자동 시작하지 않는다.
- Mac의 소형 MLP 정책 추론은 NumPy로 제공하고, 학습 결과와의 수치 일치를 검증한다.
- 오픈소스는 필요한 단계에서만 조사·설치한다. 버전/라이선스와 출처를 기록한다.

## 첫 회차

문서 기준 커밋 후 C01만 구현한다: Python 3.12 최소 패키지, 잠금 의존성,
128×128m / 0.2초 YAML 설정, 잘못된 지도 폭 거부 테스트, 실행 안내.
uv로 의존성을 잠그고 가상환경을 구성한다. 기능 코드는 최소로 유지한다.
테스트 통과 후 상태와 C01 커밋을 push하고 종료한다. 다음 작업은 C02.

원본 번들 SHA-256: `32a9859c137e4d566c6159508c9d02eaf41a828ae9a5cda57cb27e480be76b40`.

## 최신 요청 — C21까지 연속 진행

사용자가 C21까지 최대한 구현하도록 승인했다. 이번 요청은 한 회차 한 Cxx 제한을
대체한다. 각 카드 순서와 완료 검증, 단계별 커밋·push는 유지한다.

C21 완료 후 다음 구현은 C22가 아니라 추가 카드 C21-L1, C21-L2 순서다.
구현 세부 결정과 잔여 출시 항목은 IMPLEMENTATION_NOTES.md를 참고한다.

## 최신 요청 — 남은 작업 전체

사용자가 나머지 작업의 연속 구현을 승인했다. 단일 카드 중단 제한을 대체하며,
검증과 체크포인트는 유지한다. 외부 계정·다운로드 접근·실기 검증이 막히면
그 항목은 미검증으로 기록하고 독립적인 로컬 구현을 계속한다.

## 저장소 변경 확정

사용자가 R2 활성화 대신 기존 Supabase 비공개 Storage를 우선하도록 선택했다.
C29의 실제 저장소 검증은 Supabase 비공개 버킷 업로드/다운로드/checksum으로 대체한다.
R2 어댑터는 선택 기능으로 유지하고 결제·활성화는 하지 않는다. Pages는 Access 기반 비공개 테스트가 우선이다.

## 오늘의 디자인 개선

사용자가 UI/전장 팔레트 분리, Geist/NanumSquare, 12px/m 픽셀 표현,
로컬 실시간 관리자 관전을 승인했다. UI→픽셀 전장→실시간 통합 순서로
검증·커밋·push한다. 원본 렌더 픽셀 고정값보다 이 외형 개선 결정이 우선한다.
게임 수치·충돌·AI 관측은 유지하며 배포와 환경 Publish는 하지 않는다.

## 2026-10-25 KST 플레이 개선 요청

사용자가 로컬 LLM 실행, 수송/원거리 교전 수정, 분대 증원, 반복 경기와
CPU 강화학습, 단순한 병사 방향 표현, 덜 밝고 복잡한 맵 개선을 승인했다.
출시 시나리오 증원/초기 자원 조정과 전투 중 정지를 허용한다.
막힌 GGUF 후보와 별도로 Mac Ollama Qwen3 0.6B 실행 경로를 제공한다.
배포는 보류한다. Mac 실기 검증은 클라우드 검사와 구분한다.

## 제병협동 확장 승인

사용자가 64명/차량10대, 전차·곡사포·대전차병·장갑/아군 포격 피해,
후보 분석→PPO 순위→LLM 지휘, SQLite 전적과 세밀한 보드게임형 미술을 승인했다.
이는 원본 비무장 차량 제한을 대체한다. 5단계 검증/커밋/push를 유지한다.
Mac 추론·Linux CPU 학습, 배포 보류와 무료 실행 조건은 유지한다.

## 자연광 2D 미술 / 10경기 진단

사용자가 반복 도트 디자인 대신 셀 명암·디더링·자연광을 이용한 고해상도
2D 전장·보병·차량 개선과 비관전 가속 10경기 및 결과 해석을 요청했다.
렌더 크기/좌표/게임 수치는 유지하고 아틀라스 내부 해상도와 재질·그림자만
개선한다. 0.2초 물리 tick을 건너뛰지 않고 대기 없이 알고리즘 HQ로
seed0–4 양쪽 시작 위치 각1회씩 진단한다. LLM/PPO 평가와 구분한다.

## 픽셀아트 재정렬 / 수송 병목 수정

사용자가 참고 이미지처럼 보이는 픽셀 군집·제한색·디더링을 요청했다.
고해상도 곡면 3D 느낌을 걷어내고 native 픽셀 + nearest 확대를 사용한다.
차량은 M1A2/M2-M3/M109A6/JLTV/FMTV/HEMTT/CH-47 외형 모티브로 표현한다.
분산 하차·주차, 양보·재탐색, 승차 FIFO와 상태 meter를 구현한다.
교통/명령 수명 변경은 rules combined-arms-2로 분리하고 기존 정책은 재학습한다.

같은 목적지로 접근한 양팀 헬기가 서로의 착륙을 막는 재현 사례를 확인했다.
엔진 착륙 예약과 대체 지점을 추가하고, 최근 명령 수와 별도로 활성 승차 예약을 보존한다.
정적 경로 실패를 숨기는 대신 교통 대기·재계획·타임아웃 이벤트로 구분해 검사한다.

## NIM / 비공개 사이트 배포 요청

사용자가 Supabase·Cloudflare·NVIDIA NIM 연결과 배포를 요청해 기존 배포 보류를 해제했다.
소형 Llama3.1 8B Instruct를 후보 ID 선택 모델로 우선 설정하며 실호출 속도는 검증 전이다.
무료/크레딧 조건 확인 없이 결제 활성화하지 않는다. 완료 경기 관전 구조를 유지한다.
SQL 테이블 없이 비공개 Storage manifest를 지원하고, Access 미설정 시 강한 비밀번호 세션을 선택적으로 사용한다.
실제 외부 배포/모델 성공과 코드·mock 검사 성공을 구분해 기록한다.

사용자가 Access 비활성화는 의도적이라고 명시했다. PUBLIC_VIEWER=true로 완료 경기 공개 관전을 허용하고 사이트 비밀번호를 요구하지 않는다. Supabase 객체/키는 비공개로 유지한다.

NIM 키 Value 수정 후 실제 지휘 JSON 성공. NIM 요청에는 enable_thinking=false를 사용한다. 사용자가 성공 시 무한 반복 CPU PPO 학습을 명시적으로 승인했다. --rounds 0 --steps 256으로 시작하며 학습에는 NIM을 호출하지 않고 정책 자동 승격도 하지 않는다.

## 학습 현황 / 고속 실행 / 다른 맵 준비

상단 공개 학습 현황을30초 보고로 제공하고 완료 학습 경기 하나를 자동 교체한다.
학습은 실제 시간 대기 없이, 리플레이는 원본tick/기본1배속으로 제공한다.
라운드별 새 정책 초기화를 수정해 직전 가중치/옵티마이저를 이어 학습한다.
최근8개+100회 기념 정책 보존, 과거 상대/규칙 상대 혼합, 지형4변형/맵 factory 주입으로 전이 준비한다.
실제 새로운 맵 전이 성공/전략 개선은 보류 평가 전까지 주장하지 않는다. 자세한 검증은 docs/training-enhancement/REPORT.md.

## T03 가독성·NIM 교사 Self-Play

원형 보병·고정 화면 px 체력바·분대 LOD·본진 표식을 적용하고, 승하차 투영 카운트/hover 사거리/발사 좌표 효과를 수정한다.
공유 PPO의 양 진영/시작 위치4조합과 고정 상대 풀을 사용한다. 매 HQ마다 양팀 익명화 NIM 교사 질의, 실패 시 양쪽 표본 폐기,64스텝 뒤 별도 모방 보조 업데이트를 적용한다.
10개 고유 완료 학습 경기마다 Release 자산 교체/다운로드 SHA 검증 후 정리한다. 작은 manifest만 training/checkpoints 브랜치에 기록한다. 모델을 Git 이력에 누적하지 않는다.
실행 경로는 data/self-play-v2로 이관하고 레거시 모델은 보존했다. 업로드 전용 uploads.github.com은 실제 Forbidden으로 차단돼 허용 초안 적용을 기다린다.

## T04 전적·명령 가독성 / 상시 CPU 조사

모든 저장된 완료 경기의 점수만 페이지형 팝업으로 제공하고 관전은 최신 완료 학습 경기 하나를 기본으로 한다.
축소 시 분대/차량 이름·명령 상태 배지와 실제 사격 기반 교전 표식을 제공한다. 화면용 명령 telemetry는 World 밖에 보존한다.
사용자에게 상시 서버가 없어 무료 클라우드를 조사한다. Pages는 PPO 실행 서버가 아니며 Oracle Always Free는 조건 미검증 후보일 뿐이다.
공식 문서 CONNECT403으로 허용 초안만 저장했다. 별도 서버 생성·유료 자원·결제는 실행하지 않았다.

## T05 전장·관전 전면 개선 / 중간 저장

사용자 승인: 차분한 전술 픽셀, 아이콘+짧은 ID, 실제 맵 재설계, 전차 범위 피해, 수동+교전 이동.
규칙 combined-arms-3 / catalog combined-arms-2 / river-districts v2. 전차 명중 시4m/최대40 HE 범위 피해, 직접 표적 중복·탑승/공중 제외, 아군 피해 유지.
새 학습은 actor만 이전한 data/self-play-v3; critic/optimizer/buffer/counter 새로 시작. v2 복구본 보존. 지원시설/포병 방향의 진영 반전 오류를 수정했다.
최종10경기 A5/B5이나 서쪽8/동쪽2. BLOCKED/TRAFFIC_TIMEOUT 잔존; 개선·균형 확보를 주장하지 않는다.
사용자가 시간상 중단·GitHub 임시 저장을 요청했다. 추가 개발/배포를 멈추며 기존 승인된 반복 학습은 유지한다. 재개는 STATE와 docs/tactical-redesign/REPORT.md·GAMES.md 참조.

2026-10-26 재개 완료: 최종 UI 배포 aac65376 및 공개 HTML/JS·전적·학습·rules3 최신 리플레이·Chromium 검증을 마쳤다. 기존 학습 worker는 중복 시작하지 않고 유지했다. 경로/교통/진영 효과 개선은 별도 후속 작업이다.

## T08 거점 선점 통계

최초 점령은 해당 중립 거점을 처음 점령 완료한 팀이다. 이후 중립화/상대 재점령/회복으로 덮어쓰지 않는다. 각 거점·선점 조합·팀 첫 점령 장소를 승패와 연결한다. 관측 정보가 없는 과거 기록은 추측하지 않고 제외/누락으로 표시한다. 이번 구현은 관측·집계이며 보상/AI 지휘/게임 규칙을 바꾸지 않는다. 선점과 승리의 상관관계를 원인 또는 학습 향상의 증거로 단정하지 않는다.

## T09 movement/viewer/independent league

User approved wheel/pinch zoom + drag pan, real sprites from20%(icons below18%), DPR<=2 screen labels and physical squad crossing recovery. Fix movement before learning expansion. New rules combined-arms-4/tactics-2; two independent PPOs exchange teams/locations, tactics10s and paired NIM30s. Initial actor warm start only; critic/optimizer/buffers fresh.200-completed-game pilot with frozen crossed evaluation and regression pause. Immutable10-game policy/50-game recovery history replaces remote overwrite; chunked transport verifies full recovery before cleanup. No new paid/permanent CPU resource. See docs/league-transition/README.md for implemented behavior and limitations.
