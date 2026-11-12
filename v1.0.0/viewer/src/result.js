// Results use recorded winners. Credit balances and displayed scores never infer a winner.
export const winnerLabel=r=>r.winner===0?'A 승리':r.winner===1?'B 승리':r.winner==null?'무승부':'승자 —';
export function scoreLabel(r){
 const mode=r.game_mode??r.mode,t=r.combat_tickets;
 if(mode==='elimination'||t)return `전투 티켓 A ${t?.[0]??'—'} : ${t?.[1]??'—'} B`;
 const a=r.scores?.[0],b=r.scores?.[1];
 if(!['conquest','capture_flag','elimination'].includes(mode)&&a===0&&b===0)return '점수 —';
 return `${mode==='capture_flag'?'탈취 점수 ':''}A ${a??'—'} : ${b??'—'} B`;
}
export function viewResult(doc){const m=doc.final?.mission??{};return {...doc.summary,game_mode:m.mode,combat_tickets:m.combat_tickets};}
