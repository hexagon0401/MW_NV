# Cloudflare + Supabase + NIM 배포 상태

## 배포 완료

- 공개 사이트: https://mw-nv.pages.dev
- 현재 production 배포: https://f536a3f6.mw-nv.pages.dev
- Cloudflare API 토큰200 active, 프로젝트 생성, 정적 파일과 Functions 업로드, deploy 단계 success 확인.
- PUBLIC_VIEWER=true로 Access/사이트 비밀번호 없이 완료 경기 관전을 제공한다. 사용자가 명시적으로 공개 접속을 승인했다.
- Python 엔진은 로컬에서 실행하고 Pages는 완료 경기 관전만 제공한다. 원격 게임 실행 서버는 포함하지 않는다.

## 남은 검증

1. **Pages 서버 키/HTTP 검증 완료:** Production에 SUPABASE_SERVICE_ROLE_KEY의 secret_text 항목을 확인한 뒤 재배포했다. 메인 HTML200, 경기 목록200, 완료 리플레이200, 없는 경기404를 확인했다. HTML에 환경 키 참조값은 없다. Python 기본 User-Agent는 Cloudflare1010을 받지만 일반 브라우저 User-Agent는 정상이다.
2. **실제 NIM 추론은 미완료:** 마지막 실제 요청은401 Unauthorized / Invalid JWT serialization이다. 기존 NvidiaNIM 비밀값의 목적지 integrate.api.nvidia.com은 게시된 설정에서 확인했다. 실제 키 값/전달 문제를 해결해야 한다. 모델 목록200은 인증 성공을 증명하지 않는다.

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

## 최신 경기·대용량 기록 검증

보병128명·차량20대로 시작한 rules2/seed0 알고리즘 HQ 경기를 완료하고
`release-rules2-seed0-full`로 등록했다. 1,170초 시뮬레이션 후 A102:B15로 종료했다.
NIM 실행 경기가 아니다. 최신 관전 링크:
https://mw-nv.pages.dev/?match=release-rules2-seed0-full

원본14,255,831바이트 업로드는401로 실패했지만 gzip1,123,550바이트는 성공했고
다운로드 SHA-256이 일치했다. 작은 manifest 인증도200이므로 큰 요청/프록시 전송
경로의 차이를 관측했으며 정확한 거부 원인은 확정하지 않았다.
업로더는1MiB 이상 JSON을 gzip(mtime=0)으로 저장하고 관전 서버가 이를 해제한다.
기존 일반 JSON도 계속 지원한다. gzip 정상/손상 자료 검사를 포함한 JS14개와
Storage 검사1개, production/Functions 빌드를 통과했다.
재배포 뒤 공개 HTML200, 목록200(2경기), 최신 리플레이200(148기물), 없는 경기404를 확인했다.
최신 raw/gzip 리플레이·모델·키·대형 로그는 Git에 저장하지 않는다.
