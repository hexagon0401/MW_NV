// Pages-only BFF. Never imported by either browser entrypoint.
import {SignJWT,jwtVerify} from 'jose';
const enc=new TextEncoder(),owner='82876856',allowed=new Set(['pause_ppo','resume_ppo']);
const cookie=(req,name)=>req.headers.get('cookie')?.split(';').map(x=>x.trim()).find(x=>x.startsWith(name+'='))?.slice(name.length+1);
const origin=env=>env.ADMIN_ORIGIN??'https://mw-nv.pages.dev';
const configured=env=>env.MW_NV_ADMIN_AUTH_ENABLED==='true'&&env.ADMIN_SESSION_SECRET?.length>=32&&env.SUPABASE_URL?.startsWith('https://')&&!!(env.SUPABASE_AUTH_API_KEY??env.SUPABASE_SERVICE_ROLE_KEY);
const response=(value,status=200)=>Response.json(value,{status,headers:{'Cache-Control':'no-store'}});
const secret=env=>enc.encode(env.ADMIN_SESSION_SECRET);
async function token(env,payload,issuer,seconds){return new SignJWT(payload).setProtectedHeader({alg:'HS256'}).setIssuer(issuer).setAudience(origin(env)).setIssuedAt().setExpirationTime(Math.floor(Date.now()/1000)+seconds).sign(secret(env));}
async function verify(req,env,name,issuer){if(!configured(env))return null;try{const {payload}=await jwtVerify(cookie(req,name)??'',secret(env),{algorithms:['HS256'],issuer,audience:origin(env)});return payload;}catch{return null;}}
export async function adminSession(req,env){const s=await verify(req,env,'__Host-mw_nv_admin','mw-nv-admin');return s?.sub===owner&&s.role==='admin'?s:null;}
function same(a,b){if(typeof a!=='string'||typeof b!=='string'||a.length!==b.length)return false;let n=0;for(let i=0;i<a.length;i++)n|=a.charCodeAt(i)^b.charCodeAt(i);return n===0;}
function mutation(req,env,s){return req.method==='POST'&&req.headers.get('origin')===origin(env)&&same(req.headers.get('X-CSRF-Token'),s.csrf);}
function setCookie(name,value,seconds,httpOnly=true,path='/'){return `${name}=${value}; Max-Age=${seconds}; Path=${path}; Secure; SameSite=${name==='mw_nv_pkce'?'Lax':'Strict'}${httpOnly?'; HttpOnly':''}`;}
async function smallBody(req,limit){const reader=req.body?.getReader();if(!reader)return '';const chunks=[];let size=0;while(true){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>limit){await reader.cancel();throw Error('too_large');}chunks.push(value);}const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}return new TextDecoder().decode(bytes);}
async function authFetch(env,path,body,fetcher){const r=await fetcher(env.SUPABASE_URL+'/auth/v1/'+path,{method:'POST',headers:{apikey:env.SUPABASE_AUTH_API_KEY??env.SUPABASE_SERVICE_ROLE_KEY,'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw Error('auth_failed');return r.json();}
async function store(env,path,method='GET',body,fetcher=fetch){if(!env.SUPABASE_URL||!env.SUPABASE_SERVICE_ROLE_KEY)throw Error('storage_unavailable');const bucket=env.REPLAY_BUCKET??'mw-nv-replays',url=env.SUPABASE_URL+'/storage/v1/object/'+(method==='GET'?'authenticated/':'')+bucket+'/'+path;const r=await fetcher(url,{method,headers:{apikey:env.SUPABASE_SERVICE_ROLE_KEY,Authorization:'Bearer '+env.SUPABASE_SERVICE_ROLE_KEY,'Content-Type':'application/json'},body:body==null?undefined:JSON.stringify(body)});if(!r.ok){const e=Error('storage_failed');e.status=r.status;throw e;}return method==='GET'?r.json():null;}
async function maybeStore(env,path,fetcher){try{return await store(env,path,'GET',undefined,fetcher);}catch(e){if([400,404].includes(e.status))return null;throw e;}}
async function handleAdmin(req,env,fetcher=fetch){
 const path=new URL(req.url).pathname;if(!path.startsWith('/api/admin/'))return response({error:'not_found'},404);
 if(path==='/api/admin/session'&&req.method==='GET'){const s=await adminSession(req,env);return response({configured:configured(env),authenticated:!!s,control_enabled:env.MW_NV_ADMIN_CONTROL_ENABLED==='true',login:s?.login??null});}
 if(path==='/api/admin/auth/login'&&req.method==='GET'){
  if(!configured(env)||new URL(req.url).origin!==origin(env))return response({error:'admin_not_configured'},503);
  const bytes=crypto.getRandomValues(new Uint8Array(32)),verifier=btoa(String.fromCharCode(...bytes)).replaceAll('+','-').replaceAll('/','_').replaceAll('=','');const digest=new Uint8Array(await crypto.subtle.digest('SHA-256',enc.encode(verifier)));const challenge=btoa(String.fromCharCode(...digest)).replaceAll('+','-').replaceAll('/','_').replaceAll('=','');
  const url=new URL(env.SUPABASE_URL+'/auth/v1/authorize');url.searchParams.set('provider','github');url.searchParams.set('redirect_to',origin(env)+'/api/admin/auth/callback');url.searchParams.set('code_challenge',challenge);url.searchParams.set('code_challenge_method','s256');url.searchParams.set('scopes','read:user');
  return new Response(null,{status:302,headers:{Location:url.href,'Set-Cookie':setCookie('mw_nv_pkce',await token(env,{verifier},'mw-nv-oauth',600),600,true,'/api/admin/auth'),'Cache-Control':'no-store'}});
 }
 if(path==='/api/admin/auth/callback'&&req.method==='GET'){
  const pending=await verify(req,env,'mw_nv_pkce','mw-nv-oauth'),code=new URL(req.url).searchParams.get('code');if(!pending||!code||code.length>4096||new URL(req.url).origin!==origin(env))return response({error:'invalid_oauth_callback'},403);
  try{const result=await authFetch(env,'token?grant_type=pkce',{auth_code:code,code_verifier:pending.verifier},fetcher);if(!result.provider_token)throw Error('provider_missing');const gh=await fetcher('https://api.github.com/user',{headers:{Authorization:'Bearer '+result.provider_token,Accept:'application/vnd.github+json','User-Agent':'MW-NV-admin'}});if(!gh.ok)throw Error('identity_failed');const user=await gh.json();if(String(user.id)!==owner)return response({error:'not_admin'},403);
   await store(env,'control/owner-login.json','PUT',{actor_id:owner,login:user.login,verified_at:Date.now()/1000,identity_source:'github-user-api'},fetcher);
   const csrf=crypto.randomUUID(),jwt=await token(env,{sub:owner,role:'admin',login:user.login,csrf,sid:crypto.randomUUID()},'mw-nv-admin',3600);const headers=new Headers({Location:'/dashboard/#control','Cache-Control':'no-store'});headers.append('Set-Cookie',setCookie('__Host-mw_nv_admin',jwt,3600));headers.append('Set-Cookie',setCookie('__Host-mw_nv_csrf',csrf,3600,false));headers.append('Set-Cookie',setCookie('mw_nv_pkce','',0,true,'/api/admin/auth'));return new Response(null,{status:303,headers});
  }catch{return response({error:'oauth_verification_failed'},403);}
 }
 const session=await adminSession(req,env);if(!session)return response({error:'authentication_required'},401);
 if(new URL(req.url).origin!==origin(env))return response({error:'origin_denied'},403);
 if(path==='/api/admin/auth/logout'){
  if(!mutation(req,env,session))return response({error:'csrf_or_method'},403);const headers=new Headers({'Cache-Control':'no-store'});headers.append('Set-Cookie',setCookie('__Host-mw_nv_admin','',0));headers.append('Set-Cookie',setCookie('__Host-mw_nv_csrf','',0,false));return new Response(null,{status:204,headers});
 }
 if(path!=='/api/admin/control')return response({error:'not_found'},404);
 if(env.MW_NV_ADMIN_CONTROL_ENABLED!=='true')return response({error:'control_disabled'},503);
 try{const status=await store(env,'control/status.json','GET',undefined,fetcher);const online=Number.isFinite(status.last_seen)&&Date.now()/1000-status.last_seen<90&&Date.now()/1000>=status.last_seen-60;
  if(req.method==='GET')return response({...status,online});
  if(!mutation(req,env,session))return response({error:'csrf_or_method'},403);
  if(req.headers.get('content-type')?.split(';')[0]!=='application/json')return response({error:'json_required'},415);
  if(Number(req.headers.get('content-length')??0)>2048)return response({error:'too_large'},413);let text;try{text=await smallBody(req,2048);}catch{return response({error:'too_large'},413);}let body;try{body=JSON.parse(text);}catch{return response({error:'invalid_json'},400);}
  const keys=['action','request_id','instance_id','run_id','expected_version'];if(!body||Array.isArray(body)||Object.keys(body).length!==keys.length||keys.some(k=>!Object.hasOwn(body,k))||!allowed.has(body.action)||!Number.isSafeInteger(body.expected_version)||body.expected_version<0||!['request_id','instance_id'].every(k=>/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(body[k]??''))||!/^[A-Za-z0-9:_-]{1,128}$/.test(body.run_id??''))return response({error:'invalid_command'},400);
  if(!online)return response({error:'agent_offline'},409);
  const old=await maybeStore(env,'control/acks/'+body.request_id+'.json',fetcher);if(old){if(keys.some(k=>old[k]!==body[k])||old.actor_id!==owner)return response({error:'id_conflict'},409);return response(old,202);}
  if(body.instance_id!==status.instance_id||body.run_id!==status.run_id||body.expected_version!==status.version)return response({error:'stale_state'},409);
  if((status.recent??[]).filter(a=>a.at>Date.now()/1000-60&&a.status!=='rejected').length>=5)return response({error:'rate_limited'},429);
  const command={...body,actor_id:owner,created_at:Date.now()/1000,expires_at:Date.now()/1000+600};const key='control/commands/'+body.request_id+'.json';try{await store(env,key,'POST',command,fetcher);}catch(e){if(![400,409].includes(e.status))throw e;const prior=await store(env,key,'GET',undefined,fetcher);if(keys.some(k=>prior[k]!==body[k])||prior.actor_id!==owner)return response({error:'id_conflict'},409);}
  return response({request_id:body.request_id,status:'queued'},202);
 }catch{return response({error:'control_unavailable'},503);}
}

export async function adminRoute(req,env,fetcher=fetch){
 let result;try{result=await handleAdmin(req,env,fetcher);}catch{result=response({error:'admin_unavailable'},503);}
 result.headers.set('Cache-Control','no-store');result.headers.set('X-Content-Type-Options','nosniff');result.headers.set('Referrer-Policy','no-referrer');result.headers.set('Content-Security-Policy',"default-src 'none'; frame-ancestors 'none'");return result;
}
