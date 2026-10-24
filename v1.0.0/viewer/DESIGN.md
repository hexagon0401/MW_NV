# MW-NV / design pass

## 시각 체계

UI는 Geist/NanumSquare와 #FEF5EF / #26413C / #D6E3F8 / #07004D를 사용한다.
전장은 별도 팔레트다: 배경 #F1F2EC, 초지 #DFE8D7, 도로 #CACFD5, 숲 #76966D,
물 #A9D9E7, 건물 #B4B1C4, A #2F6FED, B #E27632, 중립 #C39A35, 윤곽 #334155.
폰트 배포본·라이선스·SHA-256은 src/assets/fonts에 포함한다. 런타임 CDN 요청이 없다.

렌더는 12px/m, 보병 12×20px(지원병 16×20), LUV 60×36, APC/TRK 84×48,
IFV 96×48, HEL 96×96이다. CH-47 시누크는 앞뒤 로터로 구분한다.
이는 외형 전용이다. 엔진의 기존 size_px, 속도, 충돌, 탑승 수치와 난수는 바꾸지 않는다.
픽셀 아틀라스와 지형 타일을 공유하며, 카메라 청크·줌별 LOD와 청크 캐시를 사용한다.

## 조작

휠 이동 / Shift+휠 가로 이동 / Ctrl 또는 ⌘+휠 확대 / 드래그 이동.
방향키 이동, Home 전체 보기, 미니맵 클릭, 패널 유닛 선택으로 해당 위치를 볼 수 있다.
hover 또는 tap으로 이름·팀·ID·상태를 표시한다. 좁은 화면에서는 A/B 패널을 접는다.
유닛을 선택해도 게임 명령은 전송하지 않는다.

## 데이터

presentation_version=2는 squads, task_state, radius_cm, 읽기용 명령 정보를 추가한다.
version=1 리플레이도 읽고, 없는 정보는 추측하지 않는다. 화면용 export의 복사본만
보완하며 원본 이벤트/상태 해시는 변경하지 않는다. 새 유닛의 이동 track과 되감기도 지원한다.

상단·좌우 패널·캔버스는 한 시점의 frame을 공유한다. 병력 수는 생존 보병 전체이며
도보/탑승/차량을 분리한다. 명령은 팀별 최근 10개의 최신 상태를 보여준다.
LIVE 중에는 재생 조작을 숨기고 LLM 대기 중 게임 시각을 유지한다.

## 검증

npm test / npm run build
node scripts/design-smoke.mjs — 폰트·좌우 패널·상태·툴팁·모바일
node scripts/pixel-smoke.mjs — 공유 아틀라스 실루엣·500 보병·GPU/JS 계측
node scripts/live-smoke.mjs — 실제 엔진 전투→SSE→병력 수와 서버 재시작 재연결

Linux headless Chromium의 SwiftShader에서는 500 보병 약 13–17FPS를 측정했다.
JS 실행은 1.5초 측정 중 약 0.05–0.07초였다. 이는 소프트웨어 GPU 환경 결과이며
실제 Intel Mac의 GPU 성능이나 30FPS 달성을 검증한 것은 아니다.

최종 회귀: Python 89개, JS 9개, 생산 빌드와 실제 Chromium desktop/mobile/tap/LIVE 재연결 검증 통과.
스크린샷은 docs/design에 보존했다. live.png는 실제 엔진을 사용한 3 대 3 저체력 테스트 월드다.
