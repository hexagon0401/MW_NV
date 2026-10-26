# 다중 전장 구현·전환 절차

기존 league-v1은 rules4/catalog2/tactics2로 보존한다. 새 실행만 rules5/catalog3/tactics3이다. 기본 엔진 상수는 구형 경기의 재개를 위해 유지하고 `engine.multi_scenario.create()`가 새 버전을 명시한다. 구형 리플레이 화면 재생과 rules4 재실행은 계속 지원하며, rules4 학습 checkpoint를 새1600입력 모델로 직접 재개하지 않는다.

## 실행

저장소에서 `cd v1.0.0` 후 Python3.12 환경과 기존 잠금 의존성을 사용한다. Mac 관전·알고리즘·NumPy 추론은 Torch가 필요 없다.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[server,inference]'
python -m server.live --scenario 3 --hq rules --port 8000
# http://127.0.0.1:8000/viewer/?mode=live
# --scenario 4: 깃발 탈취·귀환 / --scenario random: seed로 재현 가능한 선택
# --policy <tactics-3.npz>: NumPy 정책 / --hq nim: 허용 후보를 NIM이 선택
```

사이트 빌드가 없으면 `cd viewer && npm ci && npm run build`를 먼저 실행한다. `--scenario`를 생략하면 기존 실행을 유지한다. 로컬 NIM 실행은 환경의 NVIDIA_API_KEY 또는 NVIDIA_API_KEY_A/B를 사용하며 키는 파일·화면에 기록하지 않는다. 학습에서는 NIM이 PPO 행동을 대신하지 않고 별도 모방 표본만 제공한다.

Linux CPU 학습 환경은 기존 `.[learning]` 고정 의존성을 사용한다. Mac에 Torch 학습을 요구하지 않는다.

```sh
# 별도 이관과 검증이 끝난 경우에만 새 학습이 시작된다.
python -m learning.mission_rollout --root data/multi-mode-v1 --legacy data/league-v1
# 중지: data/multi-mode-v1/VALIDATION_STOP 또는 실행 중 학습의 STOP
# 복구: 같은 명령. 변경된 코드의 진단 결과는 다른 폴더에 보존하고 다시 검증한다.
```

`rollout-status.json`은 현재 단계를, `engine-audit.json`은30개 전체 경기와 명령 재실행 해시를, `migration-retention.json`은 각 구형/신형 정책의 맵2 보류 평가를 기록한다. 통과 전에 기존 worker를 중단하거나 모델을 대체하지 않는다. 능력 유지가 불확실하면 별도의 추가20seed를 확인하고, 여전히 미확인 또는 퇴보이면 기존 학습을 유지한다.

전환 시 기존 worker의 소비된 PPO 업데이트 경계를 기다리고 최종 전체 복구본의 업로드·다운로드·체크섬·격리 로딩을 확인한다. 실패하면 기존 실행을 재개하고 혼합 실행을 보류한다. 환경 자체가 종료되면 프로세스는 계속 돌지 않는다. 이 구현은 새 상시 서버를 생성하지 않는다.

## 정책과 경기

- 두 모델은 가중치·optimizer·교사 버퍼·추론 RNG가 독립이다. 모델을 맵별로 분리하지 않는다.
- 한 블록96경기: 각 모드32, 맞대결48/과거24/알고리즘24. 학습 진영·시작 위치를 균형 배정한다.
- 전술10초, 최대4명령. NIM 교사30초, 실패하면 양팀 표본을 함께 건너뛴다.
-64전역+64×24후보=1600입력,65행동. 후보 공유 인코더·masked mean/max pooling, actor/critic 분리. NumPy 내보내기와 후보 순열 일치를 검사한다.
- 구형 PPO1/PPO2는 각각 별도로 학습 전용 맵2 표본에서 일치하는 명령의 분포만 이관한다. 신규 행동을 구형 행동으로 추정하지 않는다. critic·optimizer는 새로 시작한다.
- 무장·가격·항공/수송/대공 능력은 opt-in 카탈로그에서 공용으로 읽는다. 신규 모드의 구매·인원 한도·유한 보급은 시나리오 설정을 따른다.
- 깃발실 벽과 출입구는 실제 이동·시야 판정이다. 차량·항공기·탑승 보병·포격으로 탈취/반납하지 못한다. 운반 중 수송은 가능하다.

## 전적·평가·복구

SQLite/JSONL의 기존 `mode`는 학습/평가/실경기 구분이다. 새 `game_mode`가 conquest/elimination/capture_flag이며 `scenario_id`와 분리한다. `/api/stats`, `/api/history`, `/api/insights`는 `game_mode`·`scenario_id` 필터를 제공한다. 전적 페이지의 offset/50개 방식과 최신 완료 리플레이 한 개는 유지한다. 구형 기록의 임무·자원은 추정하지 않는다.

명령 기회/선택/접수/완료/실패, 자원·손실·정체, 항공 손실·대공 운용, 침투·깃발 탈취/운반 거리/수송/손실/회수/귀환 이벤트를 저장한다. 전체 관전 데이터는 AI에게 제공되지 않으며, 적 운반자 ID·정확한 위치는 현재 관측에 있을 때만 입력된다.

192경기 파일럿은 검증 후 시작하며96경기마다 각 모드별5seed×팀2×위치2를 초기 고정 정책·알고리즘과 평가한다. 평가에서는 교사·경험 수집·업데이트가 없다. 초기 평가 worker와 학습 worker는 각각 CPU1thread를 사용한다. 모드별 seed단위95% 구간 전체가−0.10 아래면 보류한다. 긍정 후보의 확인 seed는 이관 불확실성 평가 seed와 분리한다. 짧은 학습/KL 감소를 전략 향상으로 해석하지 않는다.

`mission_transfer.py`는 외부 scenario_factory의 계약/통행 검증, 새 지형20000–20019의 추가 학습 전 평가와6000–6099의 동일 예산 추가 학습을 제공한다. 실제 새 지형 전이 성과는 아직 검증되지 않았다.

정책/통계는10완료경기 또는24업데이트, 전체 복구는50경기 또는120업데이트마다 불변 Release 자산으로 보존한다. 기존512KiB 분할 전송·재다운로드 검증을 재사용한다. 모델·키·대형 로그는 Git에 넣지 않는다. 복구는 `learning.league_archive restore`로 빈 새 폴더에 수행하고 검증 게이트·환경·두 optimizer·교사/RNG를 이어받는다.

## 검증 상태

실제 결과는 validation.json·browser.json·geometry.json·distillation-ppo*.json·source-archive.json을 읽는다. 실행 중인30경기 진단, 이관 유지 평가,192경기 파일럿은 완료된 정적/회귀 검사와 구분한다. Chromium 측정은 클라우드 SwiftShader이며 실제 Intel Mac 성능을 의미하지 않는다.
