import {cloudRequest} from '../../src/cloud-data.js';
export async function onRequestGet({env}){
 try{const data=await cloudRequest(env,'/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/training-status.json');const age=Date.now()-Date.parse(data.updated_at);const stale=!Number.isFinite(age)||age>90000||age< -60000;return Response.json(stale?{...data,last_recorded_status:data.status,last_recorded_phase:data.phase,status:'stale',phase:'stale',stale:true}: {...data,stale:false},{headers:{'Cache-Control':'no-store'}});}
 catch{return new Response('Training status unavailable',{status:503,headers:{'Cache-Control':'no-store'}});}
}
