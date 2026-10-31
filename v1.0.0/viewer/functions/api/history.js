import {resultView} from '../../src/results-filter.js';
import {cloudRequest} from '../../src/cloud-data.js';
export async function onRequestGet({env,request}){
 const u=new URL(request.url),offset=Number(u.searchParams.get('offset')??0),limit=50;
 if(!Number.isSafeInteger(offset)||offset<0)return new Response('Invalid offset',{status:400});
 try{
 const base='/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/';
 const d=resultView(await cloudRequest(env,base+'results-index.json'),u);const high=Math.max(0,d.total-offset),low=Math.max(0,high-limit),items=[];
 for(let page=Math.floor(low/d.page_size);page<=Math.floor((high-1)/d.page_size)&&high>low;page++){
  const rows=await cloudRequest(env,base+d.pages[page]);const start=page*d.page_size;items.push(...rows.slice(Math.max(0,low-start),Math.min(rows.length,high-start)));
 }
 return Response.json({total:d.total,updated_at:d.updated_at,items:items.reverse(),next:low>0?offset+limit:null},{headers:{'Cache-Control':'no-store'}});
 }catch{return new Response('Results unavailable',{status:503});}
}
