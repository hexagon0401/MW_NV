# CPU 학습과 Mac 정책 추론

Linux 클라우드에서 v1.0.0으로 이동:

    uv sync --locked --extra dev --extra learning
    python -m learning.evaluate --policy random --count 50 --output data/random.json
    python -m learning.evaluate --policy rules --count 50 --output data/rules.json
    python -m learning.train --steps 256
    python -m learning.selfplay
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m learning.report

처음 명령부터 학습·평가는 모두 CPU다. 기본 256 step은 통합 검증용 작은 예산이며
학습 성능 향상을 보장하지 않는다. 더 긴 학습은 별도 예산을 정한 뒤 수행한다.
selfplay는 policy0→B policy1→A policy2 순서로 이전 상대를 동결한다.
이미 있는 policy1/2는 덮어쓰지 않는다. 새 실험은 별도 데이터 경로를 선택한다.

훈련 seed 0–49, 기준선 1000–1049, 평가 10000–10099를 분리한다.
Random/Heuristic/PPO 모두 같은 20개 행동(분대 4개 × 목표 5개)과 30초 주기를 쓴다.
숨겨진 적 좌표를 관측 벡터에 포함하지 않는다. invalid action은 안전한 유효 행동으로 대체한다.
보상은 각 라운드 점수 차의 변화/100으로, 두 팀은 반대 보상을 받는다.

Intel Mac은 최신 PyTorch 학습을 지원한다고 가정하지 않는다. 대신:

    uv sync --locked --extra inference
    python -c 'from learning.policies import NumpyPolicy; print("NumPy inference available")'

data/policies의 작은 .npz를 안전하게 옮겨 NumpyPolicy로 읽는다(allow_pickle=False).
256-step 결과 가중치와 .zip 체크포인트는 Git에 넣지 않는다.
정책 로그릿/마스크 행동은 PyTorch 구현과 자동 비교한다. 실제 Mac 실기 검증은 별도다.
로컬 LLM 경기는 PyTorch나 PPO 없이도 실행되며 모델 실패 시 규칙 HQ로 복구한다.
