# T05: 전장·관전 개선 기준

선택: 차분한 전술 픽셀 / 아이콘+짧은 ID / 실제 맵 구조 변경 / 전차 범위 피해 / 수동+교전 이동.

| 확인된 문제 | 적용 방법 | 검증 |
|---|---|---|
| 두 줄92×36태그가 지도 가림 | 아이콘22px+충돌 시 ID 생략 | 6% 전체보기 |
| 태그와 실제 위치 괴리 | 실제 위치 고정, 동종 군집 | 앵커/선택 일치 |
| 병종 구별 어려움 | 전용 병종 실루엣·범례 | 차량/보병 hover |
| 명령 단계 위계 부족 | 행동/목표/상태, 실패 사유 펼침 | 단계/키보드 |
| 지도/패널 선택 불일치 | 선택 링/경로/패널 연결 | 양방향 선택 |
| 학습 줄 과밀 | 요약+접이식 상세 | 모바일/높이 |
| 축소 단색 셀 | 상세 합성 지도 | 전환 비교 |
| 반복 격자/나무 | 연결 타일·불규칙 군락 | 3개 구역 |
| 원/선 전투 효과 | 무기별 프레임 아틀라스 | 정지/역탐색 |
| 교전/추적 동선 부족 | 최근교전·추적/수동 해제 | 조작 회귀 |

읽은 참고 자료(2026-10-25, GitHub 공개 원문):
- https://github.com/mapbox/mapbox-gl-js/blob/main/src/symbol/collision_index.ts : 우선순위·충돌 억제. 구현 복사 없이 원리 적용.
- https://github.com/godotengine/godot-docs/blob/master/tutorials/2d/using_tilesets.rst : terrain 연결과 경계.
- https://github.com/godotengine/godot-docs/blob/master/tutorials/2d/2d_sprite_animation.rst : 프레임 시트.
- https://github.com/OpenRA/OpenRA/wiki/Pixelart : 일관된 팔레트/시트. OpenRA 게임 자산은 가져오지 않음.
일반 웹 출처 Mapbox/PixiJS/Lospec/Kenney는 CONNECT403이었으므로 읽었다고 간주하지 않는다.

기존 학습은 SIGINT로 종료하고 마지막 소비된 PPO rollout checkpoint를 보존한다. 규칙 변경 후 actor만 이전하고 critic/optimizer는 초기화한다.
