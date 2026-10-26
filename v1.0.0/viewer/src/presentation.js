import {TYPES,typeOf} from './catalog.js';
export function clock(tick){const seconds=Math.floor(tick/5);return `${Math.floor(seconds/60).toString().padStart(2,'0')}:${(seconds%60).toString().padStart(2,'0')}`;}
export function project(frame){return {clock:clock(frame.tick),scores:frame.scores,teams:[0,1].map(team=>{
 const all=frame.units.filter(u=>u.team===team),living=all.filter(u=>u.alive!==false),soldiers=living.filter(u=>typeOf(u).kind==='infantry'),vehicles=living.filter(u=>typeOf(u).kind==='vehicle'&&u.type_id!=='AA_SITE');
 const counts={alive:soldiers.length,operating:soldiers.filter(u=>frame.units.find(v=>v.id===u.carrier_id)?.type_id==='AA_SITE').length,onboard:soldiers.filter(u=>u.carrier_id!=null&&frame.units.find(v=>v.id===u.carrier_id)?.type_id!=='AA_SITE').length,on_foot:soldiers.filter(u=>u.carrier_id==null).length,vehicles:vehicles.length,disabled:all.filter(u=>u.alive===false).length};
 const roster=Object.entries(TYPES).map(([id,profile])=>({id,name:profile.name,count:living.filter(u=>u.type_id===id).length}));
 const orders=(frame.orders??[]).filter(c=>c.team===team&&c.op!==0).sort((a,b)=>Number(['QUEUED','RUNNING','ACCEPTED'].includes(b.status))-Number(['QUEUED','RUNNING','ACCEPTED'].includes(a.status))||(b.accepted_tick??0)-(a.accepted_tick??0)||b.cmd_id-a.cmd_id).slice(0,10);
 const squads=(frame.squads??[]).filter(s=>s.team===team).map(s=>({...s,living:living.filter(u=>s.member_ids.includes(u.id)).length}));
 return {team,counts,roster,orders,squads,units:living,objectives:frame.facilities.filter(f=>f.kind==='OBJECTIVE')};
 })};}
