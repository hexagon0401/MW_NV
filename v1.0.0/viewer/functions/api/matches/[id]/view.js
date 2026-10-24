import {matchView} from '../../../../src/cloud-data.js';
export async function onRequestGet({env,params}){try{return Response.json(await matchView(env,params.id),{headers:{'Cache-Control':'private, no-store'}});}catch{return new Response('Replay unavailable',{status:404});}}
