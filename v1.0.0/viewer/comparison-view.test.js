import {test} from 'node:test';import assert from 'node:assert/strict';import {gzipSync} from 'node:zlib';
import {onRequestGet} from './functions/api/comparisons/[id]/view.js';
const env={SUPABASE_URL:'https://example.test',SUPABASE_SERVICE_ROLE_KEY:'fixture'},sha='a'.repeat(64);
test('only completed comparison objects in dedicated prefix are served',async t=>{
 t.mock.method(globalThis,'fetch',async url=>url.endsWith('/latest.json')?Response.json({key:`comparisons/test/${sha}.json.gz`,sha256:sha}):new Response(gzipSync(JSON.stringify({summary:{ended:true}}))));
 const r=await onRequestGet({env,params:{id:'test'}});assert.equal(r.status,200);assert.equal((await r.json()).publication_id,sha);
});
test('comparison traversal and foreign objects are rejected',async t=>{
 assert.equal((await onRequestGet({env,params:{id:'../bad'}})).status,400);
 t.mock.method(globalThis,'fetch',async()=>Response.json({key:'other/private.json.gz'}));assert.equal((await onRequestGet({env,params:{id:'test'}})).status,404);
});
