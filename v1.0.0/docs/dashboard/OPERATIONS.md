# T15 운영과 데이터 계약

별도 Vite entry와 Pages 읽기 API: `/dashboard/`,
`/api/dashboard/{summary,history,trends,analysis,resources}`.
범위24h/7d/30d/all, 경기 종류, 맵2/3/4, 학습자 필터를 검증한다.
전적은50행씩 불변 revision에 고정한다. 현재 전적의 정책 버전을 펼쳐본다.

SQLite `data/results.sqlite`의 기존 records는 변경하지 않는다. rowid watermark로
완료 전적과 새 학습량을 한 번만 역산·증분 수집한다. 과거 시간/맵/배정이 없는
기록은 추정하지 않는다. 팀 승률과 실제 배정된 PPO 학습자 승률을 구분한다.
학습 추세는 현재 run/rules별이며 다른 규칙의 수치를 향상으로 합치지 않는다.

`server.dashboard_service`의 collect/publish/control 세 프로세스가 각각 독립
flock을 사용한다. collect30초, publish60초, control5초. 학습 계산 루프는
네트워크 요청을 기다리지 않는다. 에이전트 재시작 명령(환경 비밀값은 외부 주입):

```
export MW_NV_ACTIVITY_ROOT=data/activity MW_NV_CONTROL_ROOT=data/control
.venv/bin/python -m server.dashboard_service --lane collect
.venv/bin/python -m server.dashboard_service --lane publish
.venv/bin/python -m server.dashboard_service --lane control
```

각 명령은 별도 세션에서 실행한다. `data/dashboard/STOP`으로 에이전트 세 개를
종료할 수 있다. 환경이 종료되면 이 프로세스와 학습은 함께 종료된다.
무료 상시 호스팅이나 Pages CPU 학습을 제공하는 변경이 아니다.

활성 경기 파일은 프로세스 시작 식별자를 검사하며 공개 응답에서 PID·경로를
제거한다. 실행/대기/정지/평가/진단을 구분한다. 환경 cgroup CPU와 메모리,
학습 프로세스 CPU·RSS를 측정한다. RSS에는 공유 메모리 중복 가능성이 있다.
최초 CPU 표본·권한 없는 지표는 —이다. 원시7일, 시간 집계90일, 차트≤240점.
과거 CPU 이력은 새로 만들지 않는다. 전적/모델 백업은 이 정리에 포함하지 않는다.

Storage의 private dashboard/에는 공개용 필드만 담는다. 페이지와 뷰는 내용
해시를 사용하고 최종 인덱스를 나중에 바꾼다. 기존+현재 참조와10분 유예 후
미참조 집계만 정리한다. history pagination revision도 고정한다.
콜렉터 heartbeat를 발행 시각으로 덮지 않으므로 수집 중단은 STALE로 보인다.

제어는 private control/ 큐를 통해 전달된다. 관리자 숫자 ID, 요청 UUID,
실행기 UUID/run ID, 단조 상태 버전, 최대10분 TTL을 검사한다. 로컬 SQLite가
idempotency와 desired state를 보존한다. 부정확한 상태에서는 제어를 닫는다.
재개는 사전에 로컬 등록된 두 실행 경로만 사용하며 입력된 셸/PID/경로는 없다.
T11 fingerprint·이관 검증을 우회하지 않는다. 재시작도 정지를 자동 해제하지 않는다.
