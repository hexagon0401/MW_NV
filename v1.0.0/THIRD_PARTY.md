# 사용한 오픈소스

실행·테스트·빌드 시 설치한 버전이다. Python과 npm 잠금 파일이 정확한 의존성을 기록한다.

| 프로젝트 | 버전 | 라이선스 | 용도 |
|---|---|---|---|
| [PyYAML](https://github.com/yaml/pyyaml) | 6.0.3 | MIT | 게임 설정 |
| [pytest](https://github.com/pytest-dev/pytest) | 8.4.2 | MIT | 엔진 검증 |
| [FastAPI](https://github.com/fastapi/fastapi) | 0.128.0 | MIT | 로컬 읽기 API |
| [PixiJS](https://github.com/pixijs/pixijs) | 8.14.3 | MIT | 픽셀 지도·유닛 렌더 |
| [Vite](https://github.com/vitejs/vite) | 7.3.1 | MIT | 관전 빌드 |
| [PettingZoo](https://github.com/Farama-Foundation/PettingZoo) | 1.25.0 | MIT | 양팀 병렬 환경 |
| [Stable Baselines3](https://github.com/DLR-RM/stable-baselines3) | 2.7.0 | MIT | CPU 학습 기반 |
| [SB3 Contrib](https://github.com/Stable-Baselines-Team/stable-baselines3-contrib) | 2.7.0 | MIT | MaskablePPO |
| [PyTorch](https://github.com/pytorch/pytorch) | 2.8.0+cpu (Linux) | BSD-3-Clause | 학습 |
| [NumPy](https://github.com/numpy/numpy) | 2.2.6 | BSD-3-Clause 및 번들별 고지 | Mac 추론 |
| [jose](https://github.com/panva/jose) | 6.1.3 | MIT | Access JWT 검증 |
| [Wrangler](https://github.com/cloudflare/workers-sdk) | 4.50.0 | MIT OR Apache-2.0 | Pages Functions 빌드·검사 |
| [Playwright](https://github.com/microsoft/playwright) | core 1.57.0 | Apache-2.0 | 실제 Chromium 검사 |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | commit 30322097581f70126705570def8810013787af47 | MIT | 로컬 CPU 모델 서버 |

llama.cpp 소스/빌드는 /workspace/llama-runtime의 의존성 캐시이며 별도 제품 저장소가 아니다.
GGUF 모델의 라이선스·출처·체크섬은 아직 검증하지 않았고 모델은 Git에 포함하지 않았다.
