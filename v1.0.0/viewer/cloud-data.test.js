import {test} from 'node:test';import assert from 'node:assert/strict';import {listMatches,matchView} from './src/cloud-data.js';
test('server-only cloud metadata and private storage lookup',async()=>{const env={SUPABASE_URL:'https://fixture.supabase.co',SUPABASE_SERVICE_ROLE_KEY:'fixture-key'};const requests=[];const fetcher=async(url,options)=>{requests.push({url,options});return Response.json(url.includes('/rest/v1/')?[{id:'m1',replay_uri:'supabase://mw-nv-replays/m1.json'}]:{summary:{ended:true}});};await listMatches(env,fetcher);assert.match(requests[0].url,/select=id,started_at/);assert.equal((await matchView(env,'m1',fetcher)).summary.ended,true);assert.match(requests.at(-1).url,/object\/authenticated\/mw-nv-replays/);await assert.rejects(matchView(env,'../private',fetcher));});
test('Storage manifest serves only completed private matches without a SQL table',async()=>{
 const env={SUPABASE_URL:'https://fixture.supabase.co',SUPABASE_SERVICE_ROLE_KEY:'fixture-key',REPLAY_MANIFEST:'storage'};
 const fetcher=async url=>Response.json(url.endsWith('/index.json')?[{id:'m2',replay_uri:'supabase://mw-nv-replays/m2.json'}]:{summary:{ended:true}});
 assert.equal((await listMatches(env,fetcher))[0].id,'m2');assert.equal((await matchView(env,'m2',fetcher)).summary.ended,true);
 await assert.rejects(matchView(env,'missing',fetcher));
 await assert.rejects(matchView(env,'m2',async url=>Response.json(url.endsWith('/index.json')?[{id:'m2',replay_uri:'supabase://mw-nv-replays/m2.json'}]:{summary:{ended:false}})));
});
test('private gzip replay preserves completed summary and units',async()=>{
 const {gzipSync}=await import('node:zlib');
 const env={SUPABASE_URL:'https://fixture.supabase.co',SUPABASE_SERVICE_ROLE_KEY:'fixture-key',REPLAY_MANIFEST:'storage'};
 const doc={summary:{ended:true},units:[{id:1}]};
 const fetcher=async url=>url.endsWith('/index.json')?Response.json([{id:'packed',replay_uri:'supabase://mw-nv-replays/packed.json.gz'}]):new Response(gzipSync(JSON.stringify(doc)));
 assert.deepEqual(await matchView(env,'packed',fetcher),doc);
 await assert.rejects(matchView(env,'packed',async url=>url.endsWith('/index.json')?Response.json([{id:'packed',replay_uri:'supabase://mw-nv-replays/packed.json.gz'}]):new Response('invalid gzip')));
});
