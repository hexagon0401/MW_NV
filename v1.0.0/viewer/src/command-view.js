import {stateOf,OPS} from './catalog.js';
const names={HEL:'헬기',MBT:'전차',IFV:'보병전투차',APC:'수송차',TRK:'보급차',SPH:'곡사포',LUV:'경차량'};
export function entityName(frame,id){
 const squad=(frame.squads??[]).find(s=>s.id===id);
 if(squad){const index=frame.squads.filter(s=>s.team===squad.team).sort((a,b)=>a.id-b.id).findIndex(s=>s.id===id)+1;return `${squad.team===0?'A':'B'}-${String(index).padStart(2,'0')} 분대`;}
 const u=frame.units.find(u=>u.id===id);
 if(u){const letter=u.team===0?'A':'B';if(names[u.type_id]){const n=frame.units.filter(v=>v.team===u.team&&v.type_id===u.type_id).sort((a,b)=>a.id-b.id).findIndex(v=>v.id===u.id)+1;return `${letter} ${names[u.type_id]} ${n}`;}const s=(frame.squads??[]).find(s=>s.member_ids.includes(id));return s?entityName(frame,s.id):`${letter} 보병`;}
 const f=(frame.facilities??[]).find(f=>f.id===id);return f?({201:'북부 통신',202:'중앙 광장',203:'남부 보급창'}[id]??(f.kind==='HQ'?`${f.owner===0?'A':'B'} 본진`:'지원 시설')):'—';
}
export function currentOrder(frame,u){return (frame.orders??[]).filter(c=>c.unit===u.id||u.members?.includes(c.unit)||(frame.squads??[]).some(s=>s.id===c.unit&&(s.member_ids.includes(u.id)||u.members?.some(i=>s.member_ids.includes(i))))).sort((a,b)=>(b.accepted_tick??0)-(a.accepted_tick??0)||b.cmd_id-a.cmd_id)[0];}
export function orderState(frame,c){
 if(['COMPLETED','FAILED','CANCELLED'].includes(c.status))return {text:{COMPLETED:'완료',FAILED:'실패',CANCELLED:'취소'}[c.status],kind:c.status.toLowerCase()};
 if(['QUEUED','ACCEPTED'].includes(c.status))return {text:'접수',kind:'accepted'};
 const u=frame.units.find(u=>u.id===c.unit)??frame.units.find(u=>(frame.squads??[]).find(s=>s.id===c.unit)?.member_ids.includes(u.id)&&u.alive!==false&&u.carrier_id==null);
 if(u?.activity==='FIRING')return {text:'교전 중',kind:'combat'};
 return {text:u&&['MOVING','PATHING','PATH_PENDING','TAKEOFF'].includes(u.task_state)?'이동 중':u&&['WAITING_TRAFFIC','BOARDING_QUEUE','WAITING_PASSENGERS'].includes(u.task_state)?'대기 중':'수행 중',kind:u?.task_state==='WAITING_TRAFFIC'?'waiting':'running'};
}
export function orderTarget(frame,c){if(c.target)return entityName(frame,c.target);if([2,7,10,14].includes(c.op)&&c.arg0!=null&&c.arg1!=null){const f=(frame.facilities??[]).find(f=>Math.hypot(f.x_cm/100-c.arg0,f.y_cm/100-c.arg1)<60);return f?entityName(frame,f.id)+' 부근':`${c.arg0}, ${c.arg1}m`;}return '';}
export function shortState(frame,u){const c=currentOrder(frame,u);return c?`${OPS[c.op]??'명령'} · ${orderState(frame,c).text}`:u.is_group?'도보 병력':stateOf(u);}
