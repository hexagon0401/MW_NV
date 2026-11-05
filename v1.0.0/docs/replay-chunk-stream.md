# 깃발전 대용량 리플레이 발행 복구

최초 깃발전은60분 종료, pickle약98MB·압축 리플레이12,503,667바이트였다. 동일 인증으로 GET/512KiB PUT은 성공했으나12.5MB PUT만HTTP401을 반환했다. 인증키 교체 대신 작은 요청으로 전송하는 경로를 사용한다.

512KiB 조각을 업로드하고 각 조각을 다시 읽어 SHA256 검증한 후 완료 manifest와 최신 참조를 발행한다. 업로드 실패 시 이전 정상 참조와 로컬 working job을 유지한다. 최근3세대 및10분 grace는 유지하고, 만료된 manifest와 연결된 조각을 함께 정리한다. Pages는 정제된 manifest 경로·순서·크기·체크섬을 검사하고 gzip을 스트리밍하며 전체JSON을 서버 메모리에 파싱하지 않는다. 기존 단일 gzip 리플레이도 지원한다.

조각은 최대40개(20MiB compressed)로 제한해 무료 Pages의 요청 예산을 넘지 않는다. 초과 시 명시적으로 발행을 거부하고 이전 참조를 유지한다. 이 한도 이상의 리플레이는 추후 별도 전송 설계가 필요하다.

학습기와 저장된 경기는 재실행하지 않는다. 고정된 별도 publication runtime으로 발행 프로세스만 교체하며 기존 release agent가 검증된 override를 복구한다. 복구용 모델과A′/B′는 변경하지 않는다.

검증:Python replay4 PASS;JS61/build PASS;valid/corrupt/path traversal/legacy streaming tests;sealed preview history fixture PASS. 실제 깃발전 발행·완료API 확인 결과는 STATE 참조.

운영 확인: 최신 index가 capture_flag/무승부/manifest 형식으로 갱신됐고 최근3개 보존. 과거 고지점령 실행의 잔여 publisher를 종료해 공유 발행 경로 경쟁을 없앴다. 관리 프로세스 복구는 PID/start identity로 확인하며 /proc/cwd 권한에 의존하지 않는다. 반복 ensure가 동일 살아 있는 publisher PID를 유지하는 실검증도 완료.

최종 실검증: 실제 Pages API 응답 전체를 다운로드·JSON 디코딩해 summary.ended=true, final.mission.mode=capture_flag, sim_seconds=3600을 확인했다. publication header도 최신 manifest checksum과 일치했다.
