# 나중에 할 설정 작업

## 1. 클라우드 환경 네트워크

현재 대화에 연결된 MW_NV 환경의 환경 설정을 연다. 저장된 초안에서 다음
추가 도메인을 확인하고 저장한 뒤 Publish한다. 기존 package_managers preset은 유지한다.

- api.github.com
- huggingface.co
- cdn-lfs.huggingface.co
- cdn-lfs-us-1.hf.co
- cas-bridge.xethub.hf.co

초안 저장은 현재 런타임 적용이나 Publish가 아니다. 완료했다고 알려주면
Codex가 모델 다운로드와 GitHub API를 다시 확인한다. 다른 다운로드 호스트가 실제
redirect로 확인되면 해당 호스트만 추가한다. 토큰이나 키를 채팅에 붙이지 않는다.

## 2. 비공개 관전 배포

Supabase 프로젝트 URL, Cloudflare 계정 ID, Pages 프로젝트명, R2 버킷명과
엔드포인트를 준비한다. 공개 관전 전에는 비공개 테스트가 사용자 기본 선택이다.
키는 환경 설정에 안전하게 등록한다. 코드의 .env.example에 값이나 비밀키를 넣지 않는다.
실제 배포 대상과 권한은 배포 파일 준비 후 확인한다. 계정이 있어도 결제/유료 자원은 만들지 않는다.

## 3. Intel Mac 실기

실제 Mac은 이 Linux 환경에서 접근할 수 없다. GitHub의 dev/v1.0.0 브랜치를
clone한 뒤 README의 설치/테스트를 실행한다. 로컬 모델 파일은 Git에 넣지 않는다.
llama-server와 GGUF의 버전/체크섬이 검증되기 전에는 임의 다운로드 파일을 실행하지 않는다.
