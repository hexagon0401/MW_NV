const json=(data,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store'}});
const enc=new TextEncoder();
export function publicHealth(row,checked,now){
 const age=row?now-row.seen:Infinity;
 const state=age>=300?'HOST_OFFLINE':age>=90?'STALE':JSON.parse(row.health).state;
 const h=row?JSON.parse(row.health):{};
 return {state,last_seen:row?.seen??null,last_progress:h.last_progress??null,last_backup:h.last_backup??null,recovery_count:h.recovery_count??0,monitor_checked_at:checked??null,lease_valid:!!row&&row.expires>now,next_action:state==='HOST_OFFLINE'?'Codex를 다시 열어 runtime bootstrap 실행':state==='RECOVERY_BLOCKED'?'복구 차단 사유를 관리자 화면에서 확인':null};
}
async function authenticate(req,env,body,now){
 if(!env.RUNTIME_HMAC_KEY||body.length>4096)return false;
 const stamp=req.headers.get('X-Runtime-Time'),id=req.headers.get('X-Runtime-Request'),sig=req.headers.get('X-Runtime-Signature');
 if(!/^\d{10}$/.test(stamp??'')||Math.abs(now-Number(stamp))>90||!/^[-a-zA-Z0-9]{16,64}$/.test(id??'')||!/^[a-f0-9]{64}$/.test(sig??''))return false;
 const key=await crypto.subtle.importKey('raw',enc.encode(env.RUNTIME_HMAC_KEY),{name:'HMAC',hash:'SHA-256'},false,['verify']);
 const bytes=Uint8Array.from(sig.match(/../g),s=>parseInt(s,16));
 return await crypto.subtle.verify('HMAC',key,bytes,enc.encode(stamp+'\n'+id+'\n'+body));
}
export async function handle(req,env,now=Math.floor(Date.now()/1000)){
 const path=new URL(req.url).pathname;
 if(req.method==='GET'&&path==='/health'){
  const row=await env.DB.prepare('SELECT * FROM runtime_lease WHERE id=1').first();const m=await env.DB.prepare('SELECT checked FROM runtime_monitor WHERE id=1').first();return json(publicHealth(row,m?.checked,now));
 }
 if(req.method!=='POST'||path!=='/lease')return json({error:'not_found'},404);
 if(Number(req.headers.get('content-length')??0)>4096)return json({error:'too_large'},413);
 const reader=req.body?.getReader();let body='',length=0;
 if(!reader)return json({error:'body_required'},400);
 while(true){const {done,value}=await reader.read();if(done)break;length+=value.length;if(length>4096){await reader.cancel();return json({error:'too_large'},413);}body+=new TextDecoder().decode(value,{stream:true});}
 if(!await authenticate(req,env,body,now))return json({error:'unauthorized'},401);
 let d;try{d=JSON.parse(body);}catch{return json({error:'json_required'},400);}
 const ident=v=>typeof v==='string'&&/^[a-zA-Z0-9:_-]{1,128}$/.test(v);
 if(!d||!['acquire','renew','release'].includes(d.action)||!ident(d.instance_id)||!ident(d.boot_id)||!ident(d.run_id))return json({error:'invalid_request'},400);
 const states=['STARTING','RESTORING','RUNNING','PAUSED','RECOVERY_BLOCKED','LEASE_LOST','OFFLINE'];
 const raw=d.health??{};if(!states.includes(raw.state))return json({error:'invalid_health'},400);
 const health=JSON.stringify({state:d.action==='release'?'OFFLINE':raw.state,last_progress:Number.isFinite(raw.last_progress)?raw.last_progress:null,last_backup:Number.isFinite(raw.last_backup)?raw.last_backup:null,recovery_count:Number.isSafeInteger(raw.recovery_count)?raw.recovery_count:0});
 const nonce=await env.DB.prepare('INSERT OR IGNORE INTO runtime_requests VALUES(?,?) RETURNING id').bind(req.headers.get('X-Runtime-Request'),now+300).first();if(!nonce)return json({error:'replayed'},409);
 let lease;
 if(d.action==='acquire')lease=await env.DB.prepare(`INSERT INTO runtime_lease VALUES(1,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET instance_id=excluded.instance_id,boot_id=excluded.boot_id,run_id=excluded.run_id,expires=excluded.expires,seen=excluded.seen,health=excluded.health WHERE runtime_lease.expires<=? OR (runtime_lease.instance_id=? AND runtime_lease.boot_id=?) RETURNING expires`).bind(d.instance_id,d.boot_id,d.run_id,now+180,now,health,now,d.instance_id,d.boot_id).first();
 else lease=await env.DB.prepare('UPDATE runtime_lease SET expires=?,seen=?,health=?,run_id=? WHERE id=1 AND instance_id=? AND boot_id=? AND expires>? RETURNING expires').bind(d.action==='release'?now:now+180,now,health,d.run_id,d.instance_id,d.boot_id,now).first();
 return lease?json({granted:true,server_time:now,lease_until:lease.expires}):json({granted:false,reason:'lease_conflict'},409);
}
export default {fetch:(req,env)=>handle(req,env),async scheduled(_controller,env){const now=Math.floor(Date.now()/1000);await env.DB.batch([env.DB.prepare('DELETE FROM runtime_requests WHERE expires<=?').bind(now),env.DB.prepare('INSERT INTO runtime_monitor VALUES(1,?) ON CONFLICT(id) DO UPDATE SET checked=excluded.checked').bind(now)]);}};
