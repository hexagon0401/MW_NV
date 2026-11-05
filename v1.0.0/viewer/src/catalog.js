export const PX_PER_M=12;
export const TYPES={
 AT:{name:'대전차 보병',size:[16,20],kind:'infantry'},MBT:{name:'전차 · M1A2 에이브럼스',size:[108,54],kind:'vehicle'},SPH:{name:'자주곡사포 · M109A6',size:[108,60],kind:'vehicle'},
 INF:{name:'기본 보병',size:[12,20],kind:'infantry'},REC:{name:'정찰 보병',size:[12,20],kind:'infantry'},SUP:{name:'지원 보병',size:[16,20],kind:'infantry'},MED:{name:'의무 보병',size:[12,20],kind:'infantry'},ENG:{name:'공병',size:[12,20],kind:'infantry'},
 BH:{name:'UH-60 블랙호크',size:[96,96],kind:'vehicle'},LB:{name:'AH-6 리틀버드',size:[60,60],kind:'vehicle'},AA:{name:'이동식 대공포',size:[84,48],kind:'vehicle'},AA_SITE:{name:'중립 대공 진지',size:[72,72],kind:'vehicle'},
 LUV:{name:'경수송차 · JLTV',size:[60,36],kind:'vehicle'},APC:{name:'장갑수송차 · FMTV',size:[84,48],kind:'vehicle'},IFV:{name:'수송형 장갑차 · M2 브래들리',size:[96,48],kind:'vehicle'},HEL:{name:'CH-47 시누크',size:[96,96],kind:'vehicle'},TRK:{name:'보급 트럭 · Oshkosh HEMTT',size:[84,48],kind:'vehicle'}
};
export const STATUS={DEPLOYING:'설치 중',PACKING:'철수 중',WAITING_TRAFFIC:'교통 대기·재탐색',BOARDING_QUEUE:'승차 대기열',ENGAGING:'사거리 내 교전',IDLE:'대기',HOLD:'경계',DEFEND:'방어',MOVING:'이동 중',ARRIVED:'도착',BLOCKED:'이동 차단',ONBOARD:'탑승 중',DISABLED:'비활성',READY:'수송 준비',TAKEOFF:'이륙 중',LANDING:'착륙 중',UNLOADING:'하차 중',WAITING_PASSENGERS:'승차 대기',FIRING:'교전 중',PATH_PENDING:'경로 확인',PATHING:'경로 확인',NO_FUEL:'연료 부족'};
export const OPS=['대기','경계','이동','점령','거점 방어','승차','하차','수송','재보급','치료','후퇴','구매','취소','표적 공격','포격','설치','철수','수리','건물 진입','임무 상호작용','대공 진지 운용','진지 이탈'];
export const ORDER_STATUS={QUEUED:'접수',RUNNING:'실행 중',ACCEPTED:'접수',COMPLETED:'완료',FAILED:'실패',CANCELLED:'취소'};
export const typeOf=u=>TYPES[u.type_id]??{name:u.type_id??'알 수 없는 유닛',size:[12,20],kind:'infantry'};
export const stateOf=u=>u.alive===false?'비활성':u.carrier_id!=null?'탑승 중':STATUS[u.activity??u.task_state]??'—';

export function configureCatalog(catalog){if(!catalog)return;for(const [kind,profiles] of [["infantry",catalog.units],["vehicle",catalog.vehicles]])for(const [id,spec] of Object.entries(profiles??{})){TYPES[id]={...TYPES[id],name:TYPES[id]?.name??id,kind,size:spec.size_px,spec};}}
