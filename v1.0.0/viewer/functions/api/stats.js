import {cloudRequest} from '../../src/cloud-data.js';
import {resultView} from '../../src/results-filter.js';
export async function onRequestGet({env,request}){try{const doc=resultView(await cloudRequest(env,'/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/results-index.json'),new URL(request.url));return Response.json(doc.summary,{headers:{'Cache-Control':'no-store'}});}catch{return new Response('Results unavailable',{status:503});}}
