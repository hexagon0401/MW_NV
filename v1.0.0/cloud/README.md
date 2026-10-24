# 비공개 관전 연동

설정 절차는 ../SETUP_ACTIONS.md, 대상 식별자는 deployment.json에 있다.

- schema.sql은 새 mw_nv_matches 테이블에 공개 경기만 익명 읽기, 관리자만 쓰기를 허용한다.
- supabase.py는 서버 전용 메타데이터 클라이언트다.
- storage.py는 S3/R2 클라이언트 주입 방식의 gzip·read-back checksum·영구 retry queue다.
- supabase_storage.py는 비공개 Supabase Storage 대안이다. 공개 버킷을 만들지 않는다.
- viewer/functions는 RS256 Access JWT를 검증한 뒤 정적 관전 및 서버 전용 조회를 허용한다.
- 현재 private object 경로 계약은 supabase://mw-nv-replays/경기.view.json이다.
  R2 선택 시 별도 바인딩/객체 조회 연결을 완료해야 한다.

실제 배포 전 로컬 검사:

    cd viewer
    npm ci
    npm test
    npm run build
    WRANGLER_SEND_METRICS=false npx wrangler pages functions build --outdir ../data/functions-build

실제 배포는 계정 API 토큰, Access 팀/AUD, 서버 전용 키를 안전하게 설정하고
무료 사용량을 확인한 뒤 지정한 mw-nv 프로젝트에 수행한다. 현재 실제 배포는 하지 않았다.
