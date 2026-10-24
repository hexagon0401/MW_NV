export async function cloudRequest(env,path,fetcher=fetch){
 if(!env.SUPABASE_URL?.startsWith('https://')||!env.SUPABASE_SERVICE_ROLE_KEY)throw Error('backend configuration missing');
 const response=await fetcher(env.SUPABASE_URL.replace(/\/$/,'')+path,{headers:{apikey:env.SUPABASE_SERVICE_ROLE_KEY,Authorization:`Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`}});
 if(!response.ok)throw Error('backend unavailable');return response.json();
}
export async function listMatches(env,fetcher=fetch){return cloudRequest(env,'/rest/v1/mw_nv_matches?select=id,started_at,winner,scores,policy_version&order=started_at.desc&limit=20',fetcher);}
export async function matchView(env,id,fetcher=fetch){
 if(!/^[A-Za-z0-9_-]{1,64}$/.test(id))throw Error('invalid match');
 const rows=await cloudRequest(env,`/rest/v1/mw_nv_matches?id=eq.${encodeURIComponent(id)}&select=replay_uri&limit=1`,fetcher);
 if(!rows.length)throw Error('match unavailable');
 const path=rows[0].replay_uri.replace(/^supabase:\/\//,'');const bucket=env.REPLAY_BUCKET??'mw-nv-replays';
 if(!path.startsWith(bucket+'/')||path.includes('..')||!/^[A-Za-z0-9_./-]+$/.test(path))throw Error('invalid replay object');
 const doc=await cloudRequest(env,'/storage/v1/object/authenticated/'+path,fetcher);
 if(!doc.summary?.ended)throw Error('match incomplete');return doc;
}
