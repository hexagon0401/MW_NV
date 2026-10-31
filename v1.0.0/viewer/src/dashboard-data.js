// Pages-only readers of precomputed private Storage documents.
import {cloudRequest} from './cloud-data.js';
const ranges=['24h','7d','30d','all'],kinds=['all','training','evaluation','hybrid','rules','demonstration','failure_replay'],scenarios=['all','2','3','4'],learners=['all','PPO1','PPO2'];
export function dashboardQuery(url){const q={};for(const [key,values] of Object.entries({range:ranges,kind:kinds,scenario:scenarios,learner:learners})){q[key]=url.searchParams.get(key)??(key==='range'?'24h':'all');if(!values.includes(q[key]))throw Error('invalid_filter');}const offset=Number(url.searchParams.get('offset')??0);if(!Number.isSafeInteger(offset)||offset<0)throw Error('invalid_offset');q.offset=offset;q.revision=url.searchParams.get('revision');if(q.revision&&!/^[0-9a-f]{64}$/.test(q.revision))throw Error('invalid_revision');return q;}
export async function dashboardData(env,url,section,fetcher=fetch){const q=dashboardQuery(url),base='/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/dashboard/';const read=key=>cloudRequest(env,base+key+'.gz',fetcher);const latest=await read('latest.json');
 if(section==='resources')return read('resources-'+q.range+'.json');
 const index=await read(q.revision?'indexes/'+q.revision+'.json':'index.json'),view=index.views?.[`${q.range}:${q.kind}:${q.scenario}:${q.learner}`];
 if(section==='history'){
  if(!view)return {updated_at:index.updated_at,total:0,items:[],next:null,revision:index.revision};const high=Math.max(0,view.total-q.offset),low=Math.max(0,high-50),items=[];
  for(let page=Math.floor(low/100);page<=Math.floor((high-1)/100)&&high>low;page++){const rows=await read(view.pages[page]),start=page*100;items.push(...rows.slice(Math.max(0,low-start),Math.min(rows.length,high-start)));}
  return {updated_at:index.updated_at,total:view.total,items:items.reverse(),next:low>0?q.offset+50:null,revision:index.revision};
 }
 const empty={summary:{training_games:0,recent_games:0,recent_a_wins:0},recent:[],learning:[],evaluation:[],learners:{},analysis:{coverage:{matches:0,recorded:0},points:[],patterns:{}}};const data=view?await read(view.document):empty;
 if(section==='analysis')return {updated_at:index.updated_at,...data.analysis};
 if(section==='trends')return {updated_at:index.updated_at,...data,scope:data.learning_scope};
 if(section!=='summary')throw Error('unknown_section');const stale=Date.now()-Date.parse(latest.updated_at)>90000;
 return {...latest,updated_at:latest.updated_at,statistics_updated_at:index.updated_at,summary:data.summary,recent:data.recent,stale};
}
