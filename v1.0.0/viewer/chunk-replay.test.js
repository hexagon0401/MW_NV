import {test} from 'node:test';import assert from 'node:assert/strict';import {gzipSync} from 'node:zlib';import {createHash} from 'node:crypto';import {matchResponse} from './src/cloud-data.js';
const hash=b=>createHash('sha256').update(b).digest('hex');
test('stream verified chunks into complete replay; reject tampering and unsafe paths',async()=>{
 const body=gzipSync(JSON.stringify({summary:{ended:true},large:'x'.repeat(10000)})),sha=hash(body),pieces=[body.subarray(0,20),body.subarray(20)],base='training-replays/'+sha;
 const manifest={schema:1,encoding:'gzip',ended:true,sha256:sha,size:body.length,chunks:pieces.map((p,i)=>({key:base+'.part'+String(i).padStart(4,'0'),size:p.length,sha256:hash(p)}))};
 const env={SUPABASE_URL:'https://fixture.supabase.co',SUPABASE_SERVICE_ROLE_KEY:'test',REPLAY_MANIFEST:'storage'};
 const fetcher=async url=>url.endsWith('index.json')?Response.json([{id:'training-latest',sha256:sha,replay_uri:'supabase://mw-nv-replays/'+base+'.manifest.json'}]):url.endsWith('manifest.json')?Response.json(manifest):new Response(pieces[Number(url.slice(-4))]);
 const response=await matchResponse(env,'training-latest',fetcher);assert.equal(response.headers.get('X-Replay-Publication'),sha);assert.equal((await response.json()).large.length,10000);
 manifest.chunks[0].sha256='0'.repeat(64);await assert.rejects((await matchResponse(env,'training-latest',fetcher)).json());
 manifest.chunks[0].key='../control/secret';await assert.rejects(matchResponse(env,'training-latest',fetcher));
});
