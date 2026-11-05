# 전적·명령 가독성 개선

사이트: https://mw-nv.pages.dev · 배포: https://9ee26e3a.mw-nv.pages.dev

## 화면 변경

- 상단에 전체 완료 경기 수와 A/B 승·무승부를 표시한다. ‘전체 전적 자세히 보기’는 스크롤 팝업으로 점수·승자 색·실행 종류·seed·규칙 버전을 보여주며 50건씩 더 읽는다. 모든 저장된 완료 경기의 전적을 제공하며, 과거에 기록하지 않은 실행은 복원하거나 추측하지 않는다.
- 기본 관전은 최신 완료 학습 경기 하나다. 전적 팝업은 과거 리플레이를 내려받지 않는다.
- 명령 카드는 부대 → 명령·목표 → 접수/이동/대기/교전/완료 상태 순서로 읽힌다. 판단 근거는 실제 선택 후보의 관측 기반 사유이며 LLM 내부 사고를 재구성한 것이 아니다. 과거 기록에 근거가 없으면 표시하지 않는다.
- 축소 시 분대·헬기·전차 등의 이름과 명령 상태를 화면 크기 기준 배지로 표시한다. 겹침은 배지 위치와 연결선으로 완화하며 클릭하면 해당 부대로 이동한다. 지형 축소 표현은 기존 16m 샘플 대신 각 4m 셀을 보존한다.
- 최근 실제 사격/탄착 위치에만 빨간 ‘교전 중’을 표시한다. 시간 정지·탐색을 따라가며 실제 계산하지 않은 전선은 그리지 않는다.

## 데이터와 엔진

완료 경기 원장은 SQLite가 기준이다. 비공개 Storage에 압축 100건 페이지와 작은 index/summary를 게시하며, 봉인된 페이지는 재전송하지 않는다. 공개 API `/api/stats`, `/api/history?offset=0`은 서버에서 읽기만 수행한다. 종료되지 않은 경기와 PPO 업데이트 기록은 승패 집계에서 제외한다.

명령 실행 시작과 선택 후보 사유는 Engine의 화면용 기록에만 추가한다. World 이벤트 원본·물리·체크섬은 변경하지 않으며, 화면 export 때 병합한다. 화면용 기록은 복구 checkpoint에도 보존한다. 구형 리플레이는 없는 정보를 만들어내지 않는다.

## 실제 검증

- 관련 Python 23개 통과; JavaScript 21개 통과. Vite production build와 Pages Functions 컴파일 성공.
- Chromium: 실제 로컬 전적 원장 및 명령/판단 fixture로 팝업·승자 색·추가 페이지·Escape·축소 배지·부대 이동·데스크톱/모바일 검사 통과. fixture 화면을 실제 NIM의 판단 품질 검증으로 취급하지 않는다. 스크린샷: overview.png, history.png, mobile.png.
- 배포된 `/api/stats`, `/api/history?offset=0`, offset=50, `/api/training` 모두 HTTP200. 확인 시점 72경기: A34승/B38승, 페이지50+22건. 이후 학습에 따라 수치는 증가한다. 응답 요약은 remote-validation.json에 보존했다.
- 기존 self-play-v2 worker 실행을 확인했다(확인 시점 generation109, 완료 학습40경기, 누적 정책13632스텝). 이는 학습 동작 확인이며 전략 개선/새 맵 전이 성공의 근거가 아니다. 모델·키·DB·대형 로그는 커밋하지 않았다.

## 상시 실행 한계

Pages는 관전/API를 제공하고 PPO는 현재 Codex CPU 환경에서 실행한다. 환경 종료 뒤 계속 실행됨을 보장하지 않는다. 무료 상시 CPU 후보 Oracle Always Free의 공식 문서는 현재 CONNECT403으로 검증하지 못했다. docs.oracle.com/www.oracle.com 허용 초안은 저장했으나 사용자 Save/Publish가 필요하다. 계정/가용량/무료 조건 확인이나 외부 서버 배포는 완료하지 않았고 결제도 하지 않았다.

ops/ALWAYS_ON.md와 ops/training.service는 외부 서버가 확보된 후 사용할 이전 안내·systemd 템플릿이다. GitHub Release 모델 백업도 uploads.github.com 차단으로 실업로드 검증이 남아 있다. 로컬 checkpoint는 유지한다. 사용량 UNKNOWN.
