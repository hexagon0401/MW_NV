# 상시 실행 구조

브라우저/Pages를 닫아도 별도 CPU 서버가 실행 중이면 학습은 계속된다. Pages는 정적 화면과 짧은 API 응답용이며, 현재 Python/PyTorch PPO 장기 프로세스를 호스팅하지 않는다. NIM도 이 프로그램의 PPO 학습 서버가 아니다. Codex는 개발용 실행 환경이라 종료되면 worker가 멈출 수 있다.

## 무료 후보와 현재 확인 한계

상시 Linux CPU VM 후보는 Oracle Cloud Always Free다. 다만 현재 환경에서 Oracle 공식 문서 요청이 CONNECT403으로 막혀 최신 무료 CPU/RAM/회수 조건을 확인하지 못했다. 무료 사용 가능·계정 자격·가용량·카드 인증·리소스 회수 정책은 공식 안내와 가입 화면에서 확인해야 한다. 24/7 무료 가용성을 보장하지 않는다.

공식 안내: https://www.oracle.com/cloud/free/ 및 https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm

GitHub Actions/Pages를 상시 학습 서버처럼 우회 사용하지 않는다. 유료 VM·계정 업그레이드·결제 활성화는 하지 않았다. 서버/계정/SSH 권한이 없으므로 실제 외부 CPU 배포는 아직 없다.

## 서버가 준비되면

1. 호환되는 Linux CPU/Python3.12에서 잠금 의존성 설치와 짧은 학습/NumPy 일치 검사를 먼저 실행한다. ARM VM이면 현재 잠금 패키지의 ARM wheel 지원을 별도 확인한다.
2. 기존 worker를 마지막 안전 checkpoint에서 중단한 뒤 data/self-play-v3 전체와 data/results.sqlite를 안전하게 이전한다. 키는 Git/채팅에 넣지 않고 대상 서버 /etc/mw-nv/training.env에 전용 사용자만 읽도록 저장한다.
3. 전용 사용자 mwnv, 저장소 /opt/MW_NV, 쓰기 가능한 /var/lib/mw-nv 경로를 준비한다. training.service는 이 경로를 기준으로 한 배포 템플릿이다. 현재 서버에 설치·활성화한 것은 아니다.
4. 서비스 환경에는 기존 NIM/Supabase/GitHub 인증과 MW_NV_PUBLISH_TRAINING=1을 설정한다. Codex 프록시 참조값은 외부 서버에서 동작하는 실제 키가 아니므로 복사하지 않는다.
5. systemd 서비스 등록 후 재부팅·비정상 종료 복구·중복 프로세스·진행 보고·백업 업로드를 검증한다. 브라우저는 기존 Pages 주소를 계속 사용한다.

전적과 마지막 완료 리플레이는 Storage에 남아 서버 중지 중에도 조회할 수 있다. 학습 상태의 보고 시각이 오래되면 실행 중이라고 단정하지 않는다.
