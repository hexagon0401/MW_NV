import {cloudRequest} from '../../../../src/cloud-data.js';
export async function onRequestGet({env,params}){
 const id=params.id;if(!/^[a-z0-9][a-z0-9-]{0,63}$/.test(id??''))return new Response('Invalid comparison',{status:400});
 try{const base='/storage/v1/object/authenticated/'+(env.REPLAY_BUCKET??'mw-nv-replays')+'/',pointer=await cloudRequest(env,base+'comparisons/'+id+'/latest.json');
 if(!new RegExp('^comparisons/'+id+'/[a-f0-9]{64}\\.json\\.gz$').test(pointer.key??''))throw Error();
 const doc=await cloudRequest(env,base+pointer.key);if(!doc.summary?.ended)throw Error();doc.publication_id=pointer.sha256;return Response.json(doc,{headers:{'Cache-Control':'no-store'}});
 }catch{return new Response('No completed comparison replay yet',{status:404});}
}
