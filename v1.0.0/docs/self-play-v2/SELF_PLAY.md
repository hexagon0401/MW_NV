# NIM 교사와 공유 Self-Play 운영

## 완료한 구조

- 기존33번 정책을 `data/self-play-v2/seed.zip/.npz`로 보존해 이관했다. 공유 PPO가 계속 학습하며 양 진영을 번갈아 맡는다. 각 seed마다 팀·시작 위치4조합을 사용해 두 변수를 결합하지 않는다.
- 경기 시작 때 고정 상대를 고른다: 기준 정책50%, 과거 정책25%, 알고리즘25%. 초기 과거 풀이 비었으면 알고리즘으로 대체한다. 기준 정책은 자동 승격하지 않는다. 상대 NumPy 파일은 최대8개다.
- 매 HQ(30초 시뮬레이션)마다 양팀 관측을 먼저 고정해 NIM에 동시에 보낸다. 모델/프롬프트/256출력토큰/30초 제한/추론 비활성 설정은 같다. 공용 NVIDIA_API_KEY 또는 NvidiaNIM을 쓰고 선택적으로 NVIDIA_API_KEY_A/B를 지원한다. 키는 절대 프롬프트·로그·모델에 넣지 않는다.
- SELF/OPPONENT, HQ기준 좌우 정규화, 임시 부대/목표/예약 ID, seeded 후보 순서, 명시적인 합법 계획 목록을 사용한다. 원래 팀 문자와 유닛 ID는 보내지 않는다. 합법 계획도 실제 후보로 재검증한다. 비공개 적 정보는 관측 밖에서 참조하지 않는다.
- 교사는 최대4개 선택을 제안하며 실제 행동은 PPO가 결정한다. 선택 시점의1056차원 관측·65개 행동 마스크·정답·팀을 기계 데이터로 저장한다. 부대/수송/보급 예약을 순차 반영한다. 한쪽 실패 시 양팀 표본을 함께 버리고 PPO는 계속 실행한다.429는 두 팀 공통 Retry-After 대기하며 키를 돌려 제한을 피하지 않는다.
- 64스텝 PPO 학습 뒤 양팀16개씩 표본32개로 actor 보조 업데이트1회를 수행한다. loss계수.05, grad clip.5, 버퍼 최대10000개다. 교사 경험을 PPO on-policy rollout으로 취급하지 않는다. critic은 이 보조 loss로 업데이트하지 않는다.
- A.json/B.json은 동일 공유 모델 참조와 실제 해당 진영의 정책 역할을 기록한다. 로컬 원자적 checkpoint와 Supabase 비공개 역할 메타데이터로 저장하며 자연어 전략 문서를 만들지 않는다.

## 경기·평가·상태

완료 경기 ID는 실행 ID+episode로 고정한다. SQLite에 이미 기록한 ID는 재시작 후 다시 집계하지 않는다. 중단/평가는 학습 경기 카운터에서 제외한다.10경기 백업과50경기 평가는 이 카운터를 사용한다.

50경기마다 보류 seed10000–10004 양 진영의 PPO 평가10경기와 NIM 참여 평가10경기를 별도로 기록한다. teacher buffer에는 넣지 않는다. 키 배치도 seed/진영에 따라 교대한다. 기존4가지 지형 변형과 외부 scenario factory를 사용한다. 새로운 임의 맵 전이 성공을 주장하지 않는다. 새 관측/규칙은 계약 검증이 필요하다.

`/api/training`은 업데이트 번호·완료 경기 수·스텝·배속·교사 수집·백업 상태를30초마다 표시한다. 실제 초기 전환에서 교사189회 수집/모방12회/완료4경기를 확인했다. 이는 전략 개선이나 진영 편향 제거의 증거가 아니다. 물리 엔진의 고정 처리 순서 등 NIM 외 요인도 별도 진영 교대 평가로 확인해야 한다.

## 복구와 백업

- 가중치/옵티마이저·NumPy 정책·교사 버퍼·엔진/후보/예약/진행 중 경기 상태·Python/NumPy/Torch RNG·Monitor 상태·A/B 참조·SQLite 전적을 저장한다.
- 세대 폴더를 완성한 뒤 current.json 포인터를 원자적으로 바꾼다. 최근2세대를 유지한다. 레거시 루트는 삭제하지 않는다. 소비 전 rollout 도중 중단된 경험은 마지막 안전 checkpoint부터 다시 수집한다. NIM 미래 응답 자체의 결정론은 보장하지 않는다.
- 완료 학습 경기10개마다 다음 PPO 업데이트 경계에서 GitHub Release `training-latest`에 세대별 tar.gz를 올린다. 다운로드 SHA256이 맞아야 최신 참조를 바꾸고 이전 Release 자산을 삭제한다. 바이너리를 Git에 커밋하지 않는다.
- `training/checkpoints` 브랜치에는 작은 manifest만 GitHub API로 기록한다. 현재 코드 작업 트리는 건드리지 않는다. 모델은 ignored data/에만 존재한다.
- 실패 시 기존 원격 자산/확인된 로컬 복구본과 최신 pending 묶음을 보존한다. 네트워크 오류가 반복돼도 pending 묶음이 무한히 쌓이지 않도록 최대2개로 제한한다.
- **외부 차단:** Release 생성은 성공했으나 `uploads.github.com` POST가 네트워크 Forbidden이었다. 허용 도메인 초안을 저장했다. 환경 설정에서 검토·저장·Publish해야 실제 업로드와 원격 다운로드 검증을 마칠 수 있다. 현재 원격 모델 백업 완료로 보고하지 않는다. 로컬 pack/restore/체크섬/오류 보존 검사는 통과했다.

## 검증

- 전체 Python136개 통과(경고1개). 마지막 변경 뒤 관련21개 및 복구8개 재검사 통과. JavaScript18개 및 production/Functions build 통과.
- NIM 양팀 실제 요청으로8개 교사 선택 표본 수집, actor 모방 업데이트 발생을 확인했다. 실패/429 양쪽 폐기, 관측 격리, 마스크, value head 미갱신, cooldown 저장을 검사한다.
- 실제 checkpoint를 다른 프로세스에서 이어 학습하여6208→6272 정책 스텝 증가를 확인했다. Gym Monitor 상태도 복구해 env reset 없이 재개한다. 파일 손상/잘못된 SHA/백업 실패 보존을 검사했다.
- 원형 보병·hover 해제·본진 버튼·분대 축약을 Chromium으로 검사했다. circles-hover.png/headquarters.png/squad-overview.png 및 READABILITY.md 참조.
- 50경기 정기 평가와10경기 원격 업로드는 아직 해당 횟수/네트워크 조건을 충족하지 않아 전체 실전 완료로 보고하지 않는다.

## 재개

먼저 runner.pid의 프로세스가 `learning.self_play`인지 확인한다. 이미 실행 중이면 중복 시작하지 않는다.

```bash
cd /workspace/MW_NV/v1.0.0
MW_NV_PUBLISH_TRAINING=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
MPLCONFIGDIR=/workspace/.cache/mpl XDG_CACHE_HOME=/workspace/.cache \
.venv/bin/python -u -m learning.self_play --root data/self-play-v2 --seed-policy data/self-play-v2/seed.zip
```

로그 data/self-play-v2/runner.log. 환경 종료 시 프로세스가 멈출 수 있다. Publish 후에도 자동으로 실행이 유지된다고 가정하지 않고 재개 지침을 따른다. 환경 시작 지침도 이 경로로 저장했다. 사용량/전략 개선은 확인하지 못했으면 UNKNOWN이다.

최종 검증에서 Supabase 비공개 A.json/B.json의200 응답, 공개 학습 상태200, 배포 HTML과 로컬 빌드 일치를 확인했다. 재시작 후 배속은 복구 전 누적 시간을 제외한 현재 프로세스 시뮬레이션 증가량으로 계산한다. 신규 스폰 차량의 탑승 게이지도 별도 검사했다.
