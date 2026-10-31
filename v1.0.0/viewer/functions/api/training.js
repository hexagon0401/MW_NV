import {cloudRequest} from '../../src/cloud-data.js';
export async function onRequestGet({env}){
 try{return Response.json(await cloudRequest(env,'/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/training-status.json'),{headers:{'Cache-Control':'no-store'}});}
 catch{return new Response('Training status unavailable',{status:503,headers:{'Cache-Control':'no-store'}});}
}
