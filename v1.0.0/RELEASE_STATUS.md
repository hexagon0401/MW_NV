# v1.0.0 release status

## 구현·검증된 로컬 기능

- C01–C21: 엔진, 팀 격리, 원자적 보급, 보병/차량/헬기와 규칙 HQ.
- 추가 보완: PURCHASE 비용/인원/상한 검사, 길막힘 우회 1회, 아군 타워 지역 시야 보너스.
- C21-L1: 로컬 LLM 프로토콜·명령 검증·양팀 결정 barrier·실패 fallback.
- C22–C27: 안전한 JSON 체크포인트/리플레이, 1024m 지도·부하 측정,
  PixiJS 관전·재생·HUD·읽기 API. Chromium 개발/생산 API 경로 검증.
- C31–C35: PettingZoo 공식 Parallel API, masked action, CPU PPO 저장/로드,
  NumPy 추론 일치, 3개 동결 정책 풀과 320개 holdout 경기 비교. 기본 정책은 rules 유지.
- Functions 보안: RS256 issuer/audience/signature 검증, 미설정 시 차단.
  실제 로컬 Pages 런타임에서 HTML/리플레이/API 익명 요청 401 확인.

새 GitHub clone의 전체 설치에서 Python 83개·JS 6개·생산 빌드 통과.
PyTorch 없는 최소 설치는 80개 통과, 선택 모듈 2개 skipped였다.

## 외부 요구사항으로 남은 항목 — 출시 완료로 표시하지 않음

- C21-L2/C36: GGUF 다운로드 접근을 열고 공식 출처·라이선스·SHA-256을 확정해야 한다.
  llama-server CPU 빌드/버전 확인은 완료했지만 실제 모델 추론과 Intel Mac 50상태 실측은 미검증이다.
- C28: Supabase 프로젝트 주소 연결 확인(키 없음 401). 실제 SQL/RLS 적용·권한 검증은 키 제공 후 수행.
- C29: R2 비활성. 사용자가 비공개 Supabase Storage를 선택했다. 실제 업로드/다운로드 검증이 필요하다.
- C30: Pages mw-nv, 계정 ID와 대상은 기록했다. Access 미설정, API token 없음으로 실제 배포는 보류.
  Access 팀 도메인·Audience와 서버 전용 Supabase 키를 Cloudflare Pages에 안전하게 설정해야 한다.
- GitHub API 403으로 PR 생성은 미완료. Git HTTPS commit/push는 정상이다.

## 실측 범위와 제품 한계

examples/benchmark.json은 제한된 100/300/500명+차량10대 부하이고,
release_match_benchmark.json은 실제 1024m 규칙 경기 2회의 시간/점수다. Mac 성능을 뜻하지 않는다.
위치 교환 후 점수가 달라지는 시드가 있어 경쟁 밸런스 보장은 하지 않는다.
작은 256-step PPO가 규칙 HQ보다 낫지 않았고, 더 긴 학습을 자동 실행하지 않았다.
ENG의 복잡한 시설 작업은 원본에서 허용한 후속 범위로 남긴다.
