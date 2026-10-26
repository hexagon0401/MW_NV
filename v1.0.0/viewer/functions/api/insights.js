import {cloudRequest} from '../../src/cloud-data.js';
export async function onRequestGet({env}){try{return Response.json(await cloudRequest(env,'/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/league-insights.json.gz'),{headers:{'Cache-Control':'no-store'}});}catch{return new Response('Learning insights unavailable',{status:503});}}
