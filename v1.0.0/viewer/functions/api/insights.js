import {cloudRequest} from '../../src/cloud-data.js';
import {filterInsights,filterStrategyInsights,summarizeStrategyHistory} from '../../src/results-filter.js';
export async function onRequestGet({env,request}){
 const url=new URL(request?.url??'https://mw-nv.pages.dev/api/insights');try{filterStrategyInsights({},url);}catch{return new Response('Invalid strategy filter',{status:400});}
 const base='/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/';
 try{const result=filterStrategyInsights(filterInsights(await cloudRequest(env,base+'league-insights.json.gz'),url),url);
  try{const index=await cloudRequest(env,base+'strategy-insights/index.json.gz'),raw=url.searchParams.get('generation');let rows=index.lifetime;
   if(raw!==null){const path=index.buckets[String(Math.floor(Number(raw)/64))];rows=path?await cloudRequest(env,base+path):[];}result.drilldown=summarizeStrategyHistory(rows,url);
  }catch{result.drilldown={complete:false,scope:'unavailable',games:null};}
  return Response.json(result,{headers:{'Cache-Control':'no-store'}});
 }catch{return new Response('Learning insights unavailable',{status:503});}
}
