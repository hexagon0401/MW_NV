import {cloudRequest} from '../../src/cloud-data.js';
import {OBJECTIVE_FILTERS,objectiveReport} from '../../src/objective-statistics.js';
export async function onRequestGet({env,request}){
 const url=new URL(request.url),filters={};
 for(const [key,value] of url.searchParams){if(!OBJECTIVE_FILTERS.includes(key)||value.length>160)return new Response('Invalid filter',{status:400});if(value)filters[key]=value;}
 try{const doc=await cloudRequest(env,'/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/objective-stats.json.gz');return Response.json(objectiveReport(doc,filters),{headers:{'Cache-Control':'no-store'}});}catch{return new Response('Objective statistics unavailable',{status:503});}
}
