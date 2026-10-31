# T18 체크포인트 병목과 상태 표시

긴 정지는 JSON의 작은 조각을 gzip level9로 반복 쓰고, 일반 업데이트마다
전체 체크포인트를 두 번 저장하던 경로에 기인했다. 완전한 JSON/gzip 계약은
유지하면서 C JSON 인코더·compact JSON·level1 압축으로 변경했다.
일반 회차의 두 번째 저장은 변경된 archive 카운터 등 작은 metadata만 원자적으로
갱신한다. 평가가 실행된 회차와 종료 시에는 전체 복구본을 계속 저장한다.
이벤트·경기·RNG·optimizer를 생략하거나 물리 tick을 건너뛰지 않는다.

저장 구간에는 모델/engine RPC를 읽지 않는15초 heartbeat를 발행한다.
학습 환경은 WAITING, dashboard는 SAVING/복구 파일 저장 중·경과 시간을 표시한다.
저장 구간 배속은 —이며, 재개 후 측정 창을 새로 시작해 낮은 배속으로 오해하지
않게 한다. 저장 실패 때도 heartbeat 스레드를 종료하고 이전 정상 pointer를 유지한다.

대표3만 이벤트 저장:1.106→0.464초(2.38배);gzip307574→371309bytes.
복원한 JSON은 동일했다. 이는 저장기 표본이며 전체 학습 처리량 향상 수치는 아니다.
일시적 메모리 버퍼와 조금 큰 파일을 사용해 저장 CPU/쓰기 호출을 줄이는 선택이다.

Python 초기16검사와 최종12검사(중복 포함),JS47/build,Chromium SAVING 검사 통과.
검사는 모델/optimizer·다중 환경·RNG 재개,NumPy parity,archive 격리복구,
일시정지와 평가 지속,heartbeat 실패 정리,metadata의 환경파일 비변경을 포함한다.
기존107경기/258세대 전체 복구본을 data/preserved에 보존하고 원격 archive를 enqueue했다.
이전 gzip 체크포인트도 그대로 읽는다. 실제 적용 상태는 live.json에 기록한다.

실제 복구된107경기/258세대의 PPO1/2 NumPy 가중치가 이전 복구본과 동일했다.
첫 다중 환경 전체 저장40.226초를 측정했고, 공개 API에서 checkpoint/경과16.2초/
STALE=false를 확인했다. 이후 learning 상태와 시뮬레이션 시간 증가를 확인했다.
이는 전체 경기 처리량 향상을 입증하는 장기 벤치마크는 아니다.
