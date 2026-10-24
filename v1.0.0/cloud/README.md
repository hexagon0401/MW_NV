# 비공개 테스트 배포 — 아직 외부 계정 검증 전

1. Supabase SQL editor에서 schema.sql 검토 후 적용한다. published 기본값은 false다.
2. R2 버킷은 private로 유지한다. 업로드 credentials는 버킷 범위로 제한한다.
3. Pages 도메인에 Cloudflare Access를 설정하고, 인증 없이 GET이 차단되는지 확인한다.
   Pages가 기본적으로 비공개인 것은 아니다. Access 확인 전 비공개 리플레이를 배포하지 않는다.
4. 사용자 제공 프로젝트·계정·버킷 정보로 환경 설정과 허용 도메인을 추가한다.
5. 익명으로 published=false 행 조회 거부, 소유자 조회 허용, 타인 쓰기 거부를 실제 API에서 검증한다.
6. viewer에서 npm ci, npm run build 후 빌드 결과만 지정한 Pages 프로젝트에 배포한다.

schema.sql은 실제 Supabase에서 아직 실행하지 않았다. 파일 존재나 정적 검사만으로
RLS가 검증됐다고 주장하지 않는다. R2 업로드/다운로드와 Access도 계정 제공 후 검증한다.
