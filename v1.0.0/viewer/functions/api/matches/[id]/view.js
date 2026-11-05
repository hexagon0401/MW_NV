import {matchResponse} from '../../../../src/cloud-data.js';
export async function onRequestGet({env,params}){try{return await matchResponse(env,params.id);}catch{return new Response('Replay unavailable',{status:404});}}
