import {cloudRequest} from './cloud-data.js';
const idPattern=/^[a-z0-9][a-z0-9-]{0,63}$/;
export async function releaseData(env,url,path,fetcher=fetch){
 const base='/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/',index=await cloudRequest(env,base+'releases/index.json',fetcher),online=Number.isFinite(index.last_seen)&&Date.now()/1000-index.last_seen<45&&Date.now()/1000>=index.last_seen-60;
 const parts=path.split('/').filter(Boolean);if(parts.length===0)return {...index,online,items:index.items.map(({event_pages,...r})=>r)};
 const [id,section]=parts;if(!idPattern.test(id)||parts.length>2)throw Error('invalid_release');const row=index.items.find(r=>r.id===id);if(!row)throw Error('not_found');
 if(!section){const {event_pages,...item}=row;return {...item,online,last_seen:index.last_seen};}
 if(section!=='events')throw Error('not_found');const parse=k=>{const v=url.searchParams.get(k);if(v===null)return null;const n=Number(v);if(!/^\d+$/.test(v)||!Number.isSafeInteger(n))throw Error('invalid_cursor');return n;},after=parse('after'),before=parse('before');if(after!==null&&before!==null)throw Error('invalid_cursor');
 const pages=(row.event_pages??[]).filter(p=>(after===null||p.last>after)&&(before===null||p.first<before)),chosen=after===null?pages.slice(-2):pages.slice(0,2);let events=[];
 for(const p of chosen){if(!new RegExp('^releases/events/'+id+'/[a-f0-9]{64}\\.json\\.gz$').test(p.path))throw Error('invalid_object');events.push(...await cloudRequest(env,base+p.path,fetcher));}
 events=events.filter(r=>(after===null||r.seq>after)&&(before===null||r.seq<before));events=after===null?events.slice(-200):events.slice(0,200);
 return {items:events,after:events.at(-1)?.seq??after,before:events[0]?.seq??before,has_older:!!events.length&&(row.event_pages?.[0]?.first??events[0].seq)<events[0].seq,online};
}
