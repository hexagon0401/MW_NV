# 섬멸전 결과 표시 교정

신고 경기: `rotation-ff005eaeb535-release-map-rotation-10-2-00000001`.
SQLite 원본: winner=0(A), scores=[0,0], combat_tickets={0:967,1:0}, termination_reason=COMBAT_EXHAUSTED. 승패는 정상이며 고지점령 점수는 섬멸전에서 증가하지 않는다. 구매 크레딧과 전투 티켓은 별개다.

경기 선택기가 모든 모드에 scores를 사용하던 표시 오류를 수정했다. 기록된 승자를 명시하고, 로드된 완료 리플레이의 final.mission에서 티켓을 표시한다. 캐시를 publication checksum으로 구분해 현재 재생과 이동하는 최신3경기 목록을 혼동하지 않는다. 모드를 확인할 수 없는 구형0:0은 점수—로 표시한다. 전적 팝업과 대시보드는 같은 포맷터를 사용한다. 엔진 점수·승자·학습 보상·기존 전적을 수정하지 않는다.

검증:JS60개 PASS, Vite build PASS. Chromium selector fixture에서 A승리/967:0 및 구형 자료 누락 표시 PASS. 고정 preview의 실제 dashboard history bundle에서 A WIN/전투 티켓967:0 PASS. 학습 프로세스는 재시작하지 않는다.
