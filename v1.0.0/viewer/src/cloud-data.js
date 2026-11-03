export async function cloudRequest(env,path,fetcher=fetch){
 if(!env.SUPABASE_URL?.startsWith('https://')||!env.SUPABASE_SERVICE_ROLE_KEY)throw Error('backend configuration missing');
 const response=await fetcher(env.SUPABASE_URL.replace(/\/$/,'')+path,{headers:{apikey:env.SUPABASE_SERVICE_ROLE_KEY,Authorization:`Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`}});
 if(!response.ok)throw Error('backend unavailable');
 if(path.endsWith('.gz'))return new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).json();
 return response.json();
}
export async function listMatches(env,fetcher=fetch){if(env.REPLAY_MANIFEST==='storage')return cloudRequest(env,'/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/index.json',fetcher);return cloudRequest(env,'/rest/v1/mw_nv_matches?select=id,started_at,winner,scores,policy_version&order=started_at.desc&limit=20',fetcher);}
export async function matchView(env,id,fetcher=fetch){
 if(!/^[A-Za-z0-9_-]{1,64}$/.test(id))throw Error('invalid match');
 const rows=env.REPLAY_MANIFEST==='storage'?(await listMatches(env,fetcher)).filter(m=>m.id===id):await cloudRequest(env,`/rest/v1/mw_nv_matches?id=eq.${encodeURIComponent(id)}&select=replay_uri&limit=1`,fetcher);
 if(!rows.length)throw Error('match unavailable');
 const path=rows[0].replay_uri.replace(/^supabase:\/\//,'');const bucket=env.REPLAY_BUCKET??'mw-nv-replays';
 if(!path.startsWith(bucket+'/')||path.includes('..')||!/^[A-Za-z0-9_./-]+$/.test(path))throw Error('invalid replay object');
 const doc=await cloudRequest(env,'/storage/v1/object/authenticated/'+path,fetcher);
 if(!doc.summary?.ended)throw Error('match incomplete');if(rows[0].sha256)doc.publication_id=rows[0].sha256;return doc;
}

// Large completed replays are streamed; never JSON.parse the full timeline in Pages.
export async function matchResponse(env,id,fetcher=fetch){
 if(!/^[A-Za-z0-9_-]{1,64}$/.test(id))throw Error('invalid match');
 if(env.REPLAY_MANIFEST!=='storage')return Response.json(await matchView(env,id,fetcher));
 const rows=await listMatches(env,fetcher),row=rows.find(r=>r.id===id);
 if(!row)throw Error('match unavailable');
 const bucket=env.REPLAY_BUCKET??'mw-nv-replays',prefix='supabase://'+bucket+'/',uri=row.replay_uri??'';
 if(!uri.startsWith(prefix))throw Error('invalid replay');
 const key=uri.slice(prefix.length);
 if(!key.endsWith('.manifest.json'))return Response.json(await matchView(env,id,fetcher));
 const sha=row.sha256;if(!/^[a-f0-9]{64}$/.test(sha??'')||key!==`training-replays/${sha}.manifest.json`)throw Error('invalid manifest');
 const base='/storage/v1/object/authenticated/'+bucket+'/',m=await cloudRequest(env,base+key,fetcher);
 if(m.schema!==1||m.encoding!=='gzip'||m.ended!==true||m.sha256!==sha||!Array.isArray(m.chunks)||!m.chunks.length||m.chunks.length>40)throw Error('invalid chunk manifest');
 let size=0;for(const [i,c] of m.chunks.entries()){
  if(c.key!==`training-replays/${sha}.part${String(i).padStart(4,'0')}`||!/^[a-f0-9]{64}$/.test(c.sha256)||!Number.isSafeInteger(c.size)||c.size<1||c.size>524288)throw Error('invalid chunk');size+=c.size;
 }if(size!==m.size)throw Error('invalid replay size');
 let i=0;const stream=new ReadableStream({async pull(controller){try{
  if(i===m.chunks.length){controller.close();return;}const c=m.chunks[i++];
  const r=await fetcher(env.SUPABASE_URL.replace(/\/$/,'')+base+c.key,{headers:{apikey:env.SUPABASE_SERVICE_ROLE_KEY,Authorization:`Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`}});if(!r.ok)throw Error('chunk unavailable');
  const bytes=await r.arrayBuffer(),digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
  if(bytes.byteLength!==c.size||digest!==c.sha256)throw Error('chunk checksum');controller.enqueue(new Uint8Array(bytes));
 }catch(e){controller.error(e);}}});
 return new Response(stream.pipeThrough(new DecompressionStream('gzip')),{headers:{'Content-Type':'application/json','Cache-Control':'private, no-store','X-Replay-Publication':sha}});
}
