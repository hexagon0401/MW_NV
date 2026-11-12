# 혼합 학습 전 고지점령 기준 모델

- A′ = PPO1, B′ = PPO2. 1,189경기, 세대 2748, tactics-2 / combined-arms-4.
- 전용 영구 Release: https://github.com/hexagon0401/MW_NV/releases/tag/capture-specialists-1189-g2748
- ppo1/ppo2 각각의 ZIP(전체 정책·optimizer)와 NPZ(NumPy 추론)를 포함. 분할 업로드 후 실제 다운로드·SHA256 검증 완료.
- 로컬: data/preserved/capture-specialists-1189-g2748 (모델은 Git 소스에 커밋하지 않음).
- 향후 혼합 정책과 비교할 때 맵2·양 진영·시작 위치·보류seed를 고정하고 학습 없이 평가한다. 200경기 기준 비교와 별개다.
- 원본을 덮어쓰지 않는다. 혼합 입력 계약 tactics-4로 이관 시 각 원본에서 대응 명령을 증류하며 critic/optimizer는 새 입력용으로 초기화한다. 두 정책을 합치지 않는다.
