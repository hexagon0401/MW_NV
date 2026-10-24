# NIM + 비공개 Pages 관전

## 현재 결과

- NIM 후보: `meta/llama-3.1-8b-instruct`. 짧은 후보 ID JSON 선택을 위한 소형 모델을 우선 선택했다. API 실호출은 네트워크 403으로 미검증이며 가장 빠르다고 실측한 것은 아니다.
- Supabase `mw-nv-replays` 비공개 버킷 생성, `initial-private-demo` 완료 경기와 manifest 업로드, read-back SHA-256 검증 성공. anon 키 조회는 거부됐다. 데모는 이전 로컬 경기이며 NIM 생성 경기라고 주장하지 않는다.
- Cloudflare 프로젝트 조회404, 생성403 Authentication error, 토큰 검증401 Invalid API Token. 배포 URL은 아직 없다.
- Pages는 완료 경기 관전만 제공한다. Python 엔진은 Mac/개발 환경에서 실행한다. 이 배포는 브라우저에서 새 경기를 실행하는 호스팅 서버를 포함하지 않는다.
- 실행 환경의 보안 프록시 참조값을 다른 서비스의 Secret으로 복사하지 않는다.

## 검증

Python NIM/기존 HQ 검사11개와 live/전술 회귀12개, JavaScript13개, Vite production build, Pages Functions build 통과. 실제 NIM 호출과 원격 Pages 인증은 미검증이다.

## 필요한 설정 (키는 채팅/Git에 넣지 않음)

1. Cloudflare → My Profile → API Tokens → Create Custom Token. Account 권한 `Cloudflare Pages: Edit`, 대상 계정 `6974fa0dd5aeb87d1c8a95cd4e85e27d`. 환경 설정의 `CLOUDFLARE_API_TOKEN`을 새 실제 토큰으로 교체한다.
2. 환경 네트워크 허용 목록에 `integrate.api.nvidia.com`을 추가하고 적용한다. NIM 키 변수는 `NVIDIA_API_KEY` 또는 기존 `NvidiaNIM`이다. NVIDIA 계정의 사용 가능 크레딧/무료 조건은 아직 확인하지 못했다. 결제 활성화나 유료 자원 생성은 하지 않았다.
3. Pages 프로젝트 `mw-nv`를 만들고 production branch를 `dev/v1.0.0`으로 둔다. Settings → Variables and Secrets → production에 실제 `SUPABASE_SERVICE_ROLE_KEY`, 충분히 무작위인 16자 이상 `MW_NV_VIEWER_PASSWORD`를 Secret으로 입력한다. preview에도 쓸 때는 별도로 입력한다. 서버 키는 VITE_ 변수로 넣지 않는다.
4. `viewer/wrangler.jsonc`의 일반 변수는 배포 설정에 포함된다. Access는 아직 활성화하지 않았다. 비밀번호 세션은 8시간, HttpOnly/Secure/SameSite 쿠키이며 비밀번호 변경 시 기존 세션은 무효가 된다. 강한 비밀번호가 없으면 Access 인증으로만 허용하고 둘 다 없으면 차단한다. 이 경량 로그인에는 전용 계정 관리/계정별 속도 제한은 없으므로 제한된 비공개 테스트용으로 사용한다.

## 배포 명령

저장소의 `dev/v1.0.0` 최신 코드를 사용한다.

```bash
cd v1.0.0/viewer
npm ci
npm test
npm run build
XDG_CONFIG_HOME=/tmp/mw-nv-wrangler WRANGLER_SEND_METRICS=false npx wrangler pages deploy dist --project-name mw-nv --branch dev/v1.0.0
```

성공 후 반환 URL에서 비밀번호 로그인, 경기 선택, 재생과 익명 `/api/matches` 401을 확인한다. 서버 로그/HTML/번들에 키가 없는지도 확인한다. 현재는 배포가 막혀 이 원격 검사를 하지 못했다.

## NIM 경기 실행 / 완료 경기 업로드

Mac에서도 Ollama나 로컬 모델 다운로드 없이 NIM에 연결할 수 있다. 환경 변수는 터미널의 안전한 입력/환경 설정으로 넣는다.

```bash
cd v1.0.0
uv run --locked --extra server --extra inference python -m server.live --hq nim
```

양팀은 자신의 관측에서 추린 최대12개 후보만 보내며 30초 시뮬레이션 간격으로 최대4개를 고른다. 응답 중에는 엔진 시간이 멈추고 잘못된 응답/시간 초과에는 알고리즘으로 복구한다. 미시 이동에는 API를 호출하지 않는다. 이전 NumPy 정책은 새 규칙과 호환되지 않으면 사용하지 않는다.

경기 종료 후 서버가 만든 `data`의 완료 `.view.json`을 다음으로 업로드한다:

```bash
uv run python -m cloud.publish --view data/완료경기.view.json --id 고유경기ID
```

현재 업로더는 단일 운영자용이며 동시에 업로드하지 않는다. manifest는 최근20개를 유지한다. SQLite 누적 전적은 엔진 로컬에 있으며 현재 Pages 배포에는 공유 전적 API를 추가하지 않았다. 공개 버킷/SQL 테이블/자동 학습 일정/유료 리소스는 만들지 않는다.
