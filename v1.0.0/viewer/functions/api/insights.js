import {cloudRequest} from '../../src/cloud-data.js';
import {filterInsights,filterStrategyInsights} from '../../src/results-filter.js';
export async function onRequestGet({env,request}){try{return Response.json(filterStrategyInsights(filterInsights(await cloudRequest(env,'/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/league-insights.json.gz'),new URL(request.url)),new URL(request.url)),{headers:{'Cache-Control':'no-store'}});}catch{return new Response('Learning insights unavailable',{status:503});}}
