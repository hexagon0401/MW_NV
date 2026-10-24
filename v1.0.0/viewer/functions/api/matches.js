import {listMatches} from '../../src/cloud-data.js';
export async function onRequestGet({env}){try{return Response.json(await listMatches(env),{headers:{'Cache-Control':'private, no-store'}});}catch{return new Response('Matches unavailable',{status:503});}}
