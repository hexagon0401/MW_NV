# 최초 관리자 GitHub 연동

공개 대시보드: https://mw-nv.pages.dev/dashboard/ . 관전 및 읽기 API는
로그인 없이 사용할 수 있다. 관리자 제어는 별도 인증이며 공개 관전 옵션으로
활성화되지 않는다. 현재 제공자 활성화와 Production 인증 설정을 마쳤다.
실제 소유자 ID82876856의 로그인을 서버에서 확인해 제어도 활성화했다.
아래 절차는 최초 설정 기록과 복구용 안내다.

1. GitHub의 Settings → Developer settings → OAuth Apps → New OAuth App
   (https://github.com/settings/applications/new)을 연다.
   Application name: `MW-NV Admin`, Homepage URL: `https://mw-nv.pages.dev`.
   Authorization callback URL:
   `https://gwxwntyxjcfbrrcpqgtj.supabase.co/auth/v1/callback`.
2. 앱을 등록하고 Client ID와 Client Secret을 복사해 Supabase 프로젝트
   Authentication → Sign In / Providers → GitHub에 입력하고 활성화한다.
   비밀값을 Git이나 채팅에 보내지 않는다. 실제 키는 이 설정 화면에만 넣는다.
3. Supabase Authentication → URL Configuration에서 Site URL을
   `https://mw-nv.pages.dev`, Redirect URLs에 아래 주소를 정확히 추가한다.
   `https://mw-nv.pages.dev/api/admin/auth/callback`
4. 운영자가 Pages Production에 32자 이상 무작위 `ADMIN_SESSION_SECRET`을
   Secret으로 넣고, viewer/wrangler.jsonc의 `MW_NV_ADMIN_AUTH_ENABLED=true`로
   배포한다. 이 값은 저장소 설정이 기준이므로 Pages 화면에서만 바꾸지 않는다.
   `SUPABASE_URL`, 기존 서버 전용 `SUPABASE_SERVICE_ROLE_KEY`가 필요하다.
   선택적으로 `SUPABASE_AUTH_API_KEY`에 공개 Auth 키를 별도로 넣을 수 있다.
5. 대시보드의 GitHub 로그인으로 `hexagon0401` 계정으로 로그인한다.
   서버는 실제 GitHub `/user` 응답 숫자 ID `82876856`을 확인한다.
   세션에는 키나 OAuth 토큰을 넣지 않으며 1시간 뒤 만료한다.
6. 소유자 로그인과 에이전트 ONLINE을 확인한 뒤에만 Production의
   viewer/wrangler.jsonc의 `MW_NV_ADMIN_CONTROL_ENABLED=true`로 제어를 열고
   재배포한다.
   제어가 닫힌 동안 CONTROL API는 503을 반환한다.

제어는 PPO 일시정지·재개만 허용한다. 일시정지는 HQ 경계까지 실행한 뒤
PPO 업데이트·로컬 복구 저장을 마치고 적용된다. 평가·진단·백업은 계속된다.
브라우저의 요청 접수와 실제 `paused` 상태는 다르므로 적용 표시를 확인한다.
Linux 에이전트가 오프라인이면 POST를 거부한다. Pages에서 학습하지 않는다.

세션은 `__Host-` HttpOnly/Secure/SameSite=Strict 쿠키, CSRF는 별도 읽기 쿠키다.
PKCE 쿠키만 외부 OAuth 복귀를 위해 Lax이며 10분 만료한다. 응답은 no-store다.
관리 로그에는 요청 ID·액션·서버가 지정한 관리자 ID·버전·결과만 저장한다.
최초 실제 로그인 검증은 private `control/owner-login.json`에 확인된 계정 ID와
시각만 남긴다. OAuth 토큰·세션·CSRF 값은 이 기록에 저장하지 않는다.

## 복구

`MW_NV_ADMIN_CONTROL_ENABLED=false`로 제어를 닫아도 저장된 PPO 정지 상태는
바뀌지 않는다. 세션 키를 교체하면 기존 관리자 세션은 만료된다. 배포 복구는
Cloudflare Pages의 이전 배포 rollback을 사용한다. 모델·전체 전적은 별도
보존되며 대시보드 캐시 정리 대상이 아니다.
