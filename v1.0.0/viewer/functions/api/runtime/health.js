export async function onRequestGet({env}){
 const url=env.RUNTIME_MONITOR_URL;
 if(!url||!/^https:\/\/[a-z0-9.-]+\.workers\.dev\/?$/.test(url))return Response.json({state:'MONITOR_UNCONFIGURED',next_action:'외부 감시 Worker 설정 필요'},{status:503,headers:{'Cache-Control':'no-store'}});
 try{const r=await fetch(url.replace(/\/$/,'')+'/health',{signal:AbortSignal.timeout(8000)});if(!r.ok)throw Error();const d=await r.json();const keys=['state','last_seen','last_progress','last_backup','recovery_count','monitor_checked_at','lease_valid','next_action'];return Response.json(Object.fromEntries(keys.map(k=>[k,d[k]??null])),{headers:{'Cache-Control':'no-store'}});}
 catch{return Response.json({state:'MONITOR_UNREACHABLE',next_action:'감시 연결 상태 확인 필요'},{status:503,headers:{'Cache-Control':'no-store'}});}
}
