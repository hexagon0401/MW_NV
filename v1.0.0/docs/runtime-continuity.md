# T29 Codex 장시간 학습 유지·복구

## 확인된 사실

대화 당시 동일한 고지점령 PID38626/시작 식별자와 활동 기록을 대조해2026-11-02 13:54경~11-03 12:14경(KST), 약22시간20분 유지 사례를 확인했다. 같은 run_id가 재사용된 전체 기록191.48시간과 이전 canary의79.41시간 범위는 중간 재시작을 배제하지 못하므로 연속 실행 시간으로 보고하지 않는다. Codex 창을 닫은 정확한 시각은 수집되지 않았다.

현재 프로세스는 start_new_session/분리 로그로 대화 종료와 독립될 수 있으나 호스트 종료를 막지는 못한다. 실제 환경 재부팅과 모든 PID 소멸이 확인됐다. 공개된 공식 Codex 원격 시작API는 현재 도구에서 확인되지 않았다. 내부API·가짜 keepalive·인증 우회는 사용하지 않는다.

## 구현과 실행

- `cd /workspace/MW_NV/v1.0.0` 후 `.venv/bin/python -m server.runtime_supervisor check`.
- 준비된 runtime-continuity를 typed Apply한 뒤 `.venv/bin/python -m server.runtime_supervisor bootstrap`. 이후15초 supervisor 검사,30초 heartbeat,180초 D1 원자적 임대. 자동 복구3회/15분. 오래 걸리는 정상 작업은 강제 종료하지 않는다.
- 임대 상실 시 새 PPO 업데이트를 막고 학습기에 안전 정지를 요청한다. 이미 실행 중인 한 번의 엔진 작업·저장은 경계까지 정리될 수 있다. 관리자 정지·소유자STOP·평가퇴보·다른Apply는 덮어쓰지 않는다.
- Boot ID/PID start/실제 명령 검증과 flock으로 중복 실행을 막는다. supervisor 자체가 종료되거나 호스트 전체가 꺼지면 Cloudflare에서 감지하지만 외부에서 Codex를 켜지는 않는다.
- Worker1/D1 DB1/5분Cron1만 사용하며 무료 확인 전 생성하지 않는다. 공개 /api/runtime/health는 생존·진전·원격 백업·복구 횟수·다음조치만 노출한다.90초 STALE/5분 HOST_OFFLINE, 감시 Worker 미설정은 MONITOR_UNCONFIGURED다.
- PPO1/PPO2·맵3→4→2의10경기 순환·보상·NIM예산은 유지한다. 기존10/50경기 보존에60분 이후 첫 안전한 업데이트 경계의 전체 백업을 추가한다. 이 값은 보장된 RPO가 아니며 마지막 **검증 완료** 시각을 따로 표시한다.
- 실행 코드도 deterministic archive로 GitHub Release에 보존한다. 전체 모델/optimizer/RNG/환경/전적/지도순환 저장본과 사설 recovery pointer를 묶는다. 새 디스크는 원격 검증된 코드/전체복구본을 내려받아 복구하며 기존 local current.json을 덮어쓰거나 모델을 초기화하지 않는다.

## 현재 외부 선행 조건과 다음 세션 명령

새 FULL ACCESS 토큰은 사용자가 입력했지만 이번 세션 종료 후 Publish해야 반영된다. 현재 인증은 Worker목록만 조회 가능하고 D1조회10000/401·계정설정/구독조회10000/403이다. Workers 최초 무료 사용 활성화와 실제 D1 권한은 아직 검증하지 못했다. 새 유료 플랜을 선택하지 않는다.

1. 세션 종료 후 Cloudflare의 Workers **무료** 사용을 시작하고, 해당 계정에 Workers Scripts:Edit·D1:Edit·Account Settings:Read가 있는 새 토큰을 Codex CLOUDFLARE_API_TOKEN에 저장·Publish한다.
2. 다음 세션에서 D1 목록 GET와 무료 조건을 재확인한다. 사용자가 Cloudflare 화면/API로 Free를 확인한 뒤 `.venv/bin/python -m scripts.deploy_runtime_monitor --confirm-free` 실행. 자동 유료 전환은 없다. 이 명령은 D1 schema/Worker/cron/key를 구성하고 새 URL을 기록한다.
3. 생성되는 ignored `data/runtime/monitor.key`와 같은 실제 값을 프로세스용 `MW_NV_RUNTIME_MONITOR_KEY`로 안전하게 저장한다. 채팅에 보내지 않는다. Proxy placeholder는 로컬 HMAC에 사용할 수 없다. 보존된 디스크에서는 key 파일을 사용한다.
4. `.venv/bin/python -m scripts.prepare_runtime_release`: 실제 서명 acquire/release 확인 후에만 monitor gate가 PASS가 된다. Pages Production의 RUNTIME_MONITOR_URL에는 배포된 workers.dev URL을 넣고 고정 사이트 배포물에 반영한다.
5. runtime-continuity READY를 typed Apply한다(사용자가 이번 구현에서 승인함). 현재18경기/g60 모델·optimizer·환경에서 이어지는지 확인한다. 실측한24시간 운영 결과만 나중에 보고한다.

환경 start_skill은 bootstrap 지침으로 저장했다. Publish는 사용자가 환경 설정에서 수행하며, 지침은 OS 부팅서비스나 외부 깨우기API가 아니다. 코드가 준비됐다는 이유만으로 미설정 monitor를 활성 또는 학습을 실행 중이라고 표시하지 않는다.

## 검증

SQLite를 사용한 D1 쿼리 검사: 동시 임대 충돌, 소유자 갱신/해제, 만료, 서명·timestamp·nonce 재전송, 공개 필드 제거, cron. Python: boot/deadline, stale PID, 실제 격리 child 종료·복구,3회 제한, 관리자정지·STOP·평가퇴보, 코드archive checksum/경로차단/재현성, 모델 복구. 실 Cloudflare D1/임대·장시간 관찰은 권한 반영 후 확인해야 한다.
