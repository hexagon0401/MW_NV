# Cloudflare + Supabase + NIM 배포 상태

## 배포 완료

- 공개 사이트: https://mw-nv.pages.dev
- 현재 production 배포: https://3d803f6f.mw-nv.pages.dev
- Cloudflare API 토큰200 active, 프로젝트 생성, 정적 파일과 Functions 업로드, deploy 단계 success 확인.
- PUBLIC_VIEWER=true로 Access/사이트 비밀번호 없이 완료 경기 관전을 제공한다. 사용자가 명시적으로 공개 접속을 승인했다.
- Python 엔진은 로컬에서 실행하고 Pages는 완료 경기 관전만 제공한다. 원격 게임 실행 서버는 포함하지 않는다.

## 남은 검증

1. **Pages 서버 키:** 사용자는 입력 완료라고 알려줬지만 재배포 후 Cloudflare API의 production env_vars에는 SUPABASE_SERVICE_ROLE_KEY가 아직 없다. Codex 환경이 아니라 Cloudflare → Workers & Pages → mw-nv → Settings → Variables and Secrets에서 Production/Secret으로 저장했는지 확인 중이다. 실제 값은 채팅/Git에 넣지 않는다. 보안 프록시 참조값을 복사하지 않는다.
2. **실제 NIM 추론:** 네트워크와 모델 목록 조회200은 통과했으나 추론은401 Unauthorized / Invalid JWT serialization이다. 기존 NvidiaNIM 비밀값의 목적지 integrate.api.nvidia.com은 게시된 설정에서 확인했다. 실제 키 값/전달 문제를 해결해야 한다.
3. **새 사이트 HTTP 검사:** 현재 Codex 네트워크가 mw-nv.pages.dev 접속을403으로 차단한다. 해당 production 도메인과 초기 배포 도메인의 허용 목록 초안을 저장했다. 환경 설정에서 저장/Publish 후 공개 HTML·경기 API·리플레이 실제 응답을 검사한다. Cloudflare의 deploy success와 실제 HTTP 검증은 구분한다.

## 모델 선택

기존 meta/llama-3.1-8b-instruct는 NVIDIA가 2026-08-26 서비스 종료했으며 실제 HTTP410으로 확인했다. 기본 후보를 현재 카탈로그에 있는 nvidia/nemotron-3.5-lightning-30b-a3b로 변경했다. 30B 전체/3B 활성 계열의 빠른 지시 모델 후보이며, 실제 속도·품질·사용 가능 크레딧은 인증 성공 전까지 UNKNOWN이다. 두 요청 모두 인증/서비스 종료 오류였으므로 오류 응답 시간을 추론 속도로 사용하지 않는다. 유료 자원/결제를 활성화하지 않았다.

## 실행과 배포 재개

```bash
# NIM 키는 환경 설정에 넣는다. 모델 파일/Ollama는 필요 없다.
cd v1.0.0
uv run --locked --extra server --extra inference python -m server.live --hq nim
# 완료 경기만 단일 운영자가 업로드한다. manifest는 최근20개.
uv run python -m cloud.publish --view data/완료경기.view.json --id 고유경기ID
# 사이트 재배포
cd viewer
npm ci
npm run build
XDG_CONFIG_HOME=/tmp/mw-nv-wrangler WRANGLER_SEND_METRICS=false npx wrangler pages deploy dist --project-name mw-nv --branch dev/v1.0.0
```

Supabase mw-nv-replays는 비공개이며 초기 데모/manifest 업로드·다운로드 체크섬과 익명 조회 거부를 확인했다. 데모는 NIM 생성 경기라고 주장하지 않는다. NIM은 팀별 관측에서 상위12개 후보를 받아 최대4개를 고르며 30초 시뮬레이션 간격에만 호출한다. 잘못된 응답/시간 초과는 알고리즘으로 복구한다. SQLite 누적 전적은 로컬에 있으며 현재 Pages에 공유 전적 서버는 없다.

이전 검사: Python HQ11+live/전술12, JS13, Vite/Pages Functions 빌드 통과. 이번 모델 기본값 변경 후 NIM2 검사 통과. 원격 HTTP·NIM 실제 성공은 미검증이다. 상세 기계 기록은 validation-status.json.
