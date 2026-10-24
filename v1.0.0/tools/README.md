# Intel Mac의 로컬 LLM 준비

현재 GGUF 다운로드가 네트워크에서 차단되어 모델 파일의 출처/라이선스/체크섬은
미검증이다. config/local-model.json의 null을 임의 값으로 채워 검증을 통과시키지 않는다.
네트워크 적용 후 후보 Qwen3.5-0.8B의 공식 가중치/라이선스와 GGUF 아티팩트를 검토해
정확한 URL과 SHA-256을 고정한다. 도구는 미검증 manifest와 손상 파일을 거부한다.

Mac에는 Git, CMake, C++ compiler(Xcode command line tools)가 필요하다.
모델 준비 후 실행할 재현 절차:

    git clone https://github.com/ggml-org/llama.cpp.git ../llama-runtime
    git -C ../llama-runtime checkout 30322097581f70126705570def8810013787af47
    cmake -S ../llama-runtime -B ../llama-runtime/build -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=OFF -DGGML_METAL=OFF -DLLAMA_CURL=OFF
    cmake --build ../llama-runtime/build --target llama-server -j 2
    python tools/model_download.py
    ../llama-runtime/build/bin/llama-server -m models/hq.gguf --host 127.0.0.1 --port 8080 -c 4096 -np 1 -t 4

다른 터미널의 v1.0.0 디렉터리에서:

    python -m engine.local_match --output data/local
    python -m agents.benchmark_local --server-pid SERVER_PID

SERVER_PID는 실제 서버 프로세스 번호로 바꾼다. 모델 서버는 게임과 같은 컴퓨터의
loopback에서 실행한다. 실제 모델이 없어도 rules fallback은 동작하지만,
그 결과를 LLM 성공으로 보고하지 않는다. Mac의 실측 50개 상태 검증은 별도로 필요하다.
