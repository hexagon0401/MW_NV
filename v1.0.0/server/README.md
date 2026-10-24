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
