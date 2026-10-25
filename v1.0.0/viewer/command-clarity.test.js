import {test} from 'node:test';import assert from 'node:assert/strict';import {entityName,orderState,orderTarget} from './src/command-view.js';import {placeBadges} from './src/badge-layout.js';import {resultLabel} from './src/history.js';
test('semantic names and command phases use actual state',()=>{
 const frame={units:[{id:10,team:0,type_id:'HEL',task_state:'MOVING'}],squads:[],facilities:[{id:202,x_cm:51200,y_cm:51200}]};
 assert.equal(entityName(frame,10),'A 헬기 1');assert.equal(orderState(frame,{unit:10,status:'RUNNING'}).text,'이동 중');assert.equal(orderState(frame,{unit:10,status:'COMPLETED'}).text,'완료');assert.equal(orderTarget(frame,{target:202}),'중앙 광장');assert.equal(resultLabel({winner:1}),'B 승리');assert.equal(resultLabel({winner:null}),'무승부');
});
test('screen labels displace overlapping labels without changing source positions',()=>{
 const input=[{id:1,x_cm:1000,y_cm:1000},{id:2,x_cm:1000,y_cm:1000}],copy=JSON.stringify(input);
 const boxes=placeBadges(input,{zoom:.1,x:100,y:100},800,600);assert.notEqual(boxes[0].y,boxes[1].y);assert.equal(JSON.stringify(input),copy);
});
test('history endpoint paginates immutable compressed pages newest first',async()=>{
 const {onRequestGet}=await import('./functions/api/history.js'),{gzipSync}=await import('node:zlib');
 const original=global.fetch;global.fetch=async url=>url.endsWith('results-index.json')?Response.json({total:250,page_size:100,pages:['p0.gz','p1.gz','p2.gz']}):new Response(gzipSync(JSON.stringify(Array.from({length:url.endsWith('p2.gz')?50:100},(_,i)=>({id:String(Number(url.match(/p(\d)\.gz$/)[1])*100+i)})))));
 try{const env={SUPABASE_URL:'https://fixture.supabase.co',SUPABASE_SERVICE_ROLE_KEY:'fixture'};
  const a=await(await onRequestGet({env,request:new Request('https://viewer/api/history?offset=0')})).json();assert.equal(a.items[0].id,'249');assert.equal(a.items.at(-1).id,'200');assert.equal(a.next,50);
  const b=await(await onRequestGet({env,request:new Request('https://viewer/api/history?offset=50')})).json();assert.equal(b.items[0].id,'199');assert.equal(b.items.at(-1).id,'150');
  assert.equal((await onRequestGet({env,request:new Request('https://viewer/api/history?offset=-1')})).status,400);
 }finally{global.fetch=original;}
});
