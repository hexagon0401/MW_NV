# 로컬 읽기 전용 관전

v1.0.0에서 실행:

    uv sync --locked --extra dev --extra server
    python -m engine.viewer_export
    cp viewer/public/demo.json data/demo.view.json
    python -m uvicorn server.app:app --host 127.0.0.1 --port 8000

다른 터미널에서 viewer 디렉터리로 이동해 npm ci 후 npm run dev를 실행한다.
관전 페이지의 match 쿼리 값 demo를 지정하면 Vite proxy를 통해 API 데이터를 읽는다.
API에 쓰기·게임 제어·임의 파일 경로 기능은 없다. 완료된 *.view.json 파일만 노출한다.
공개 서버 배포용 인증은 별도 구성하며 여기서는 loopback에만 바인딩한다.

# 로컬 진행 경기 관전

일반 API가 8000 포트를 사용 중이면 먼저 종료한 뒤 v1.0.0에서:

    uv sync --locked --extra server --extra dev
    python -m server.live --seed 1 --hq rules --port 8000

viewer 디렉터리에서 npm run dev를 실행한 후 '진행 경기'를 선택한다.
생산 빌드를 로컬 API로 읽을 때도 viewer 경로에서 mode=live를 선택할 수 있다.
로컬 모델 서버가 준비되어 있다면 --hq local --endpoint http://127.0.0.1:8080/v1을 사용한다.
모델 응답을 기다리는 동안 시간은 정지하고 UI에 'HQ 판단 중'이 표시된다.

GET /live/snapshot 및 /live/events(SSE)는 이 실행 모드에서만 추가된다.
/api/live/... 별칭도 지원한다. 호스트·Origin을 loopback으로 제한하고 기본 CORS를 유지한다.
스트림은 bootstrap map+snapshot 후 최대 5Hz의 최신 상태만 보낸다. 재연결은 최신 snapshot부터
복구하며 무제한 이벤트 대기열을 쌓지 않는다. 이 전체 전황은 로컬 관리자 관전용이고
HQ 정책의 개별 관측과 공유하지 않는다. 진행 경기는 기존 /matches에 노출하지 않는다.

경기가 종료되면 data/live-*.view.json 및 재생 가능한 *.replay.json을 기록한다.
중간 실행 중인 경기는 공개 파일로 저장하지 않는다. 서버 종료는 그 서버의 경기만 중지한다.
클라우드 Pages에는 진행 경기 엔드포인트를 추가하지 않으며 이번 작업에서는 배포하지 않았다.

CLI는 종료 신호를 받으면 경기 소유 스레드와 SSE를 먼저 중지한다. 종료 대기에는
2초 제한을 두며, 브라우저는 서버 재시작 후 최신 snapshot으로 다시 연결한다.
