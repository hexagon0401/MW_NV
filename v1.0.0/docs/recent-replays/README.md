# 최근 3개 완료 리플레이

관전 상단 경기 선택기에 최신/2번째/3번째 최근 경기를 표시한다. 목록 갱신
(모바일↻),30초 폴링, 탭 복귀로 catalog만 갱신한다. 현재 timeline·시간·카메라를
바꾸지 않는다. 새 경기 보기 버튼은 명시적으로 최신 alias로 이동한다.
이전 경기를 보다가 최신을 눌러도 과거 query를 다시 불러오지 않는다.

latest alias는 유지하고 과거2개는 payload SHA 기반의 불변 ID로 노출한다.
서버가 payload를 업로드·다운로드 SHA 검증한 후 index를 바꾼다. 동일 payload
재발행은 중복 슬롯을 만들지 않는다. 123→234→345로 목록을 이동하며, 최근3개
밖으로 나간 파일은 퇴출 시각부터10분 유예 후 삭제한다. 이미 브라우저에
다운로드한 timeline은 끝까지 재생된다. 오래된 선택은 읽기 불가한 링크 대신
현재 재생 중/보관기간 밖으로 표시한다. 전체 경기 ledger/승패 기록은 삭제하지 않는다.

Storage에 남아 있던 payload를 SHA 검증 후 재연결해 기존3개를 복원했다.
Python3검사: 슬라이딩/불변ID/중복/유예/깨진 업로드/이전 pointer 유지.
JavaScript47검사와 build 통과. Chromium에서3→4→5 목록, 과거 선택,
갱신 중 재생 시간·카메라 유지, 퇴출된 현재 timeline 유지, 최신 query 복귀,
모바일 버튼 화면 내 배치/클릭을 확인했다(browser.json).

학습 엔진/정책/optimizer는 변경하지 않았다. 새 publisher를 로드하기 위해
발행 lane만 재시작했다. T11 완료 진단13개를 보존하고, publication 모듈 외
전체 runtime 파일 SHA가 동일함을 검사해 재검증 지문과 연결했다.
진단기의 미완료 사례는 다시 수행한다. 모델 학습 프로세스는 유지했다.
근거:runtime-revalidation.json. Production 검사는 production.json.
