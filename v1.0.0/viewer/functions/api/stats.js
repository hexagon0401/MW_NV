import {cloudRequest} from '../../src/cloud-data.js';
export async function onRequestGet({env}){try{const doc=await cloudRequest(env,'/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/results-index.json');return Response.json(doc.summary,{headers:{'Cache-Control':'no-store'}});}catch{return new Response('Results unavailable',{status:503});}}
