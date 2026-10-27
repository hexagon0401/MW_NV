// Server-only typed release requests. Session/Origin are checked by admin-server.
export async function releaseAdmin(req,env,session,helpers,fetcher){
 const {response,mutation,smallBody,store,maybeStore}=helpers;
 if(env.MW_NV_RELEASE_CONTROL_ENABLED!=='true')return response({error:'release_control_disabled'},503);
 if(!mutation(req,env,session))return response({error:'csrf_or_method'},403);
 if(req.headers.get('content-type')?.split(';')[0]!=='application/json')return response({error:'json_required'},415);
 let body;try{body=JSON.parse(await smallBody(req,2048));}catch{return response({error:'invalid_or_large_body'},400);}
 const keys=['request_id','release_id','content_digest','action','enabled'];
 if(!body||Array.isArray(body)||Object.keys(body).length!==keys.length||keys.some(k=>!Object.hasOwn(body,k))||!['apply','set_auto','rollback'].includes(body.action)||!/^[a-z0-9][a-z0-9-]{0,63}$/.test(body.release_id??'')||!/^[a-f0-9]{64}$/.test(body.content_digest??'')||!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(body.request_id??'')||(body.action==='set_auto'?typeof body.enabled!=='boolean':body.enabled!==null))return response({error:'invalid_release_command'},400);
 try{
  const index=await store(env,'releases/index.json','GET',undefined,fetcher),item=index.items?.find(r=>r.id===body.release_id),online=Date.now()/1000-index.last_seen<45;
  if(!item||item.content_digest!==body.content_digest)return response({error:'stale_release'},409);
  const old=await maybeStore(env,'releases/acks/'+body.request_id+'.json',fetcher);
  if(old){if(keys.some(k=>old.request_fields?.[k]!==body[k]))return response({error:'id_conflict'},409);return response(old,202);}
  if(body.action!=='set_auto'&&!online)return response({error:'agent_offline'},409);
  if(body.action==='apply'&&item.status!=='READY'||body.action==='rollback'&&item.status!=='APPLIED')return response({error:'release_not_ready'},409);
  const now=Date.now()/1000,command={...body,actor_id:session.sub,created_at:now,expires_at:body.action==='set_auto'?null:now+600},key='releases/commands/'+body.request_id+'.json';
  try{await store(env,key,'POST',command,fetcher);}catch(e){if(![400,409].includes(e.status))throw e;const prior=await store(env,key,'GET',undefined,fetcher);if(keys.some(k=>prior[k]!==body[k]))return response({error:'id_conflict'},409);}
  return response({request_id:body.request_id,status:'queued'},202);
 }catch{return response({error:'release_queue_unavailable'},503);}
}
