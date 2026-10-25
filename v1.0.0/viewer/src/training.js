export function describeTraining(data,now=Date.now()){
 if(!data||!Number.isFinite(Date.parse(data.updated_at)))return '학습 현황 — 연결 확인 불가';
 const stale=now-Date.parse(data.updated_at)>180000;
 return `${stale?'마지막 보고 · ':''}${({checkpoint_saved:'체크포인트 저장',evaluation:'보류 평가 중',stopped:'학습 중지'})[data.phase]??'PPO 학습 중'} · 업데이트 ${data.round} · 완료 ${data.games??0}경기 · 누적 완료 ${Number(data.completed_steps??0).toLocaleString()}스텝 · 정책 ${Number(data.policy_steps??0).toLocaleString()}스텝 · 시뮬레이션 ${data.sim_speed??'—'}× · ${data.maps??'—'} · ${data.map_id?data.map_id+' v'+data.map_version:'맵 —'} · CPU · ${data.nim_in_training?`NIM 교사 · ${data.teacher?.paired??0}회 수집`:'NIM 미사용'} · ${data.backup==='verified'?'백업 검증됨':data.backup?.startsWith('deferred')?'백업 재시도 대기':'10경기 백업 대기'} · ${new Date(data.updated_at).toLocaleTimeString('ko-KR')}`;
}
export function startTrainingStatus(){
 const label=document.getElementById('training-text');if(!label)return;
 async function refresh(){try{const r=await fetch('/api/training',{cache:'no-store'});if(!r.ok)throw Error();const data=await r.json();const full=describeTraining(data);const old=Date.now()-Date.parse(data.updated_at)>180000;label.textContent=`${old?'마지막 보고':data.phase==='stopped'?'학습 중지':data.phase==='evaluation'?'평가 중':'PPO 학습'} · 완료 ${data.games??0}경기 · ${data.sim_speed??'—'}×`;document.getElementById('training-full').textContent=full;}catch{label.textContent='학습 현황 — 연결 확인 불가';}}
 refresh();const timer=setInterval(refresh,30000);window.addEventListener('pagehide',()=>clearInterval(timer),{once:true});
}
