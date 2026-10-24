export const PX_PER_M=12;
export const TYPES={
 INF:{name:'기본 보병',size:[12,20],kind:'infantry'},REC:{name:'정찰 보병',size:[12,20],kind:'infantry'},SUP:{name:'지원 보병',size:[16,20],kind:'infantry'},MED:{name:'의무 보병',size:[12,20],kind:'infantry'},ENG:{name:'공병',size:[12,20],kind:'infantry'},
 LUV:{name:'경수송차',size:[60,36],kind:'vehicle'},APC:{name:'장갑수송차',size:[84,48],kind:'vehicle'},IFV:{name:'수송형 장갑차',size:[96,48],kind:'vehicle'},HEL:{name:'CH-47 시누크',size:[96,96],kind:'vehicle'},TRK:{name:'보급 트럭',size:[84,48],kind:'vehicle'}
};
export const STATUS={IDLE:'대기',HOLD:'경계',DEFEND:'방어',MOVING:'이동 중',ARRIVED:'도착',BLOCKED:'이동 차단',ONBOARD:'탑승 중',DISABLED:'비활성',READY:'수송 준비',TAKEOFF:'이륙 중',LANDING:'착륙 중',UNLOADING:'하차 중',WAITING_PASSENGERS:'승차 대기',FIRING:'교전 중',PATH_PENDING:'경로 확인',PATHING:'경로 확인',NO_FUEL:'연료 부족'};
export const OPS=['대기','경계','이동','점령','거점 방어','승차','하차','수송','재보급','치료','후퇴','구매','취소'];
export const ORDER_STATUS={QUEUED:'접수',RUNNING:'실행 중',ACCEPTED:'접수',COMPLETED:'완료',FAILED:'실패',CANCELLED:'취소'};
export const typeOf=u=>TYPES[u.type_id]??{name:u.type_id??'알 수 없는 유닛',size:[12,20],kind:'infantry'};
export const stateOf=u=>u.alive===false?'비활성':u.carrier_id!=null?'탑승 중':STATUS[u.task_state]??'—';
