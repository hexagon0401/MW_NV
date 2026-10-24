# 다음에 할 설정 — 이 문서를 보며 진행

## 1. Codex 환경 설정 저장/Publish

현재 대화에 연결된 MW_NV 클라우드 환경의 환경 설정을 연다.
이미 저장된 초안에서 아래 도메인과 변수·키 요구사항을 확인한다.
기존 package_managers preset을 유지하고 저장한 뒤 Publish한다.
초안 저장만으로 실행 환경이나 스냅샷이 적용됐다고 가정하지 않는다.

추가 도메인:
- api.github.com
- huggingface.co
- cdn-lfs.huggingface.co
- cdn-lfs-us-1.hf.co
- cas-bridge.xethub.hf.co
- gwxwntyxjcfbrrcpqgtj.supabase.co
- api.cloudflare.com

저장된 일반 값:
- SUPABASE_URL=https://gwxwntyxjcfbrrcpqgtj.supabase.co
- CLOUDFLARE_ACCOUNT_ID=6974fa0dd5aeb87d1c8a95cd4e85e27d
- CLOUDFLARE_PAGES_PROJECT=mw-nv

환경 설정의 안전한 키 입력란에 입력할 값(채팅/Git에 보내지 않음):
- SUPABASE_SERVICE_ROLE_KEY: Supabase 프로젝트 설정 API Keys의 서버 전용 legacy service_role key.
- SUPABASE_ANON_KEY: 같은 곳의 legacy anon key. 실제 RLS 익명 조회 거부 테스트에 사용.
- CLOUDFLARE_API_TOKEN: 계정 범위를 제한한 Pages 편집 토큰. R2 활성화/유료 리소스 권한은 필요 없다.

다른 모델 다운로드 호스트가 redirect로 확인되면 그 호스트만 추가한다.
완료 후 이 대화에 '환경 설정 적용 완료'라고 알려주면 다운로드/API/RLS를 재검증한다.

## 2. Supabase 데이터 준비

현재 프로젝트 주소는 연결되며 키가 없어서 HTTP 401이 반환됐다.
Dashboard의 SQL Editor에서 cloud/schema.sql을 검토하고 실행한다.
이 스크립트는 새 앱 테이블 mw_nv_matches 전용이다. 같은 이름의 기존 운영 테이블이
있으면 바로 적용하지 말고 현재 구조부터 확인한다.
공개 읽기는 published=true에만 허용하고 쓰기는 서버 관리자 키에만 허용한다.

사용자가 선택한 Supabase Storage에 비공개 버킷 mw-nv-replays를 준비한다.
public을 끄고 무료 저장량/전송량의 남은 한도를 확인한다. R2는 현재 비활성이다.
활성화나 결제를 자동 진행하지 않는다. 실제 업로드·다운로드 checksum은 계정 준비 후 검증한다.

## 3. Cloudflare의 비공개 Pages 준비

계정 ID는 위 값, 프로젝트는 mw-nv다. 계정 표시 이름 hexagon0401과 계정 ID는 다르다.

1. Pages 프로젝트에서 실제 서비스/preview 도메인을 확인한다.
2. Cloudflare Zero Trust의 Access Applications에 해당 도메인의 애플리케이션을 구성한다.
   비공개 테스트용 허용 정책은 본인 또는 정해진 테스트 사용자로 제한한다.
3. Access의 팀 도메인과 Application Audience(AUD)를 확인한다.
4. Pages 프로젝트의 서버 환경에 ACCESS_TEAM_DOMAIN(예: 팀명.cloudflareaccess.com),
   ACCESS_AUDIENCE를 설정한다. 서버 전용 SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
   REPLAY_BUCKET=mw-nv-replays도 설정한다. 서비스 키는 Cloudflare의 암호화된 secret으로 입력한다.
   Codex의 프록시 placeholder를 복사하지 말고 실제 키를 해당 서비스의 안전한 UI에 입력한다.
5. 설정 완료를 알려주면 Codex가 인증/미인증 접근, Functions와 실제 스토리지 연결을 검증한다.

Pages Functions는 위 Access 설정/JWT가 없으면 HTML·경기 JSON·API를 차단한다.
로컬 실제 Pages 런타임에서 익명 401을 확인했지만, 실제 Cloudflare 배포/정책은 아직 미검증이다.

## 4. Intel Mac에서 실제 모델 확인

README대로 dev/v1.0.0을 clone하고 tests를 실행한다.
tools/README.md의 고정 llama.cpp 버전으로 CPU 서버를 빌드한다.
Linux에서는 빌드와 --version을 확인했지만 Mac 실행은 별도 검증이 필요하다.
GGUF는 공식 출처·라이선스·SHA-256을 확인한 뒤 manifest를 확정한다.
모델 서버와 게임을 동시에 실행해 50개 상태의 유효율·지연·메모리를 측정한다.
