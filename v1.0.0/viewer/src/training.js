export function describeTraining(data,now=Date.now()){
 if(!data||!Number.isFinite(Date.parse(data.updated_at)))return '학습 현황 — 연결 확인 불가';
 const stale=now-Date.parse(data.updated_at)>180000;
 return `${stale?'마지막 보고 · ':''}${data.phase==='checkpoint_saved'?'체크포인트 저장':'PPO 학습 중'} · ${data.round}회차 · 누적 완료 ${Number(data.completed_steps??0).toLocaleString()}스텝 · 정책 ${Number(data.policy_steps??0).toLocaleString()}스텝 · 시뮬레이션 ${data.sim_speed??'—'}× · ${data.maps??'—'} · CPU · NIM 미사용 · ${new Date(data.updated_at).toLocaleTimeString('ko-KR')}`;
}
export function startTrainingStatus(){
 const label=document.getElementById('training-text');if(!label)return;
 async function refresh(){try{const r=await fetch('/api/training',{cache:'no-store'});if(!r.ok)throw Error();label.textContent=describeTraining(await r.json());}catch{label.textContent='학습 현황 — 연결 확인 불가';}}
 refresh();const timer=setInterval(refresh,30000);window.addEventListener('pagehide',()=>clearInterval(timer),{once:true});
}
